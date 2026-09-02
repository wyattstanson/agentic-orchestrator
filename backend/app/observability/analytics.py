"""Aggregate cost & performance across all past traces."""

from __future__ import annotations

from collections import Counter

from .store import TraceStore


def _walk_tools(span, counter: Counter) -> None:
    if span.get("agent") == "tool":
        counter[span["name"].removeprefix("tool:")] += 1
    for child in span.get("children", []):
        _walk_tools(child, counter)


def aggregate(store: TraceStore) -> dict:
    traces = store.all()
    n = len(traces)
    if n == 0:
        return {
            "tasks": 0,
            "total_cost_usd": 0.0,
            "avg_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "total_tokens": 0,
            "escalation_rate": 0.0,
            "tool_usage": [],
            "recent": [],
        }

    total_cost = sum(t.total_cost_usd for t in traces)
    total_latency = sum(t.duration_ms for t in traces)
    total_tokens = sum(t.total_tokens for t in traces)
    escalated = sum(1 for t in traces if t.escalations > 0)

    tools: Counter = Counter()
    for t in traces:
        for root in t.spans:
            _walk_tools(root.model_dump(), tools)

    recent = [
        {
            "task_id": t.task_id,
            "request": t.request,
            "cost_usd": t.total_cost_usd,
            "duration_ms": t.duration_ms,
            "created_at": t.created_at,
        }
        for t in traces[:12]
    ]

    return {
        "tasks": n,
        "total_cost_usd": round(total_cost, 6),
        "avg_cost_usd": round(total_cost / n, 6),
        "avg_latency_ms": round(total_latency / n, 2),
        "total_tokens": total_tokens,
        "escalation_rate": round(escalated / n, 3),
        "tool_usage": [{"tool": k, "count": v} for k, v in tools.most_common()],
        "recent": recent,
    }
