"""Run the dataset through the orchestrator and report metrics.

Reports success rate, escalation rate, avg cost, and avg latency broken down by
category and complexity tier — plus the headline result: memory recall coverage
on repeated task families (the 2nd/3rd occurrence recalls the first).
"""

from __future__ import annotations

from statistics import mean
from typing import Any

from app.dataset.schema import AgenticTask
from app.llm.base import LLMProvider
from app.memory import HashingEmbedder, LocalLongTermMemory
from app.observability import Trace


def _plan_tokens(trace: Trace) -> int:
    for span in trace.spans:
        if span.name == "plan":
            return span.tokens_in + span.tokens_out
    return 0


def run_harness(
    tasks: list[AgenticTask],
    *,
    provider: LLMProvider | None = None,
    limit: int | None = None,
    memory_path: str | None = None,
) -> dict[str, Any]:
    # A dedicated, shared long-term memory so recall accumulates across the run.
    from tempfile import mkdtemp

    from app.orchestration import Orchestrator

    path = memory_path or (mkdtemp(prefix="eval_mem_") + "/mem.json")
    longterm = LocalLongTermMemory(HashingEmbedder(), path)

    subset = tasks[:limit] if limit else tasks
    rows: list[dict[str, Any]] = []
    family_seen: dict[str, int] = {}

    for task in subset:
        orch = Orchestrator(provider=provider, longterm=longterm)
        events = list(orch.stream_run(task.request, task_id=task.task_id))
        done = next((e for e in events if e["type"] == "done"), None)
        recall = next((e for e in events if e["type"] == "memory_recall"), None)
        failed = any(
            e["type"] == "subtask_done" and e["status"] == "failed" for e in events
        )
        has_final = any(e["type"] == "final" for e in events)
        trace = orch.tracer.trace

        occ = family_seen.get(task.family, 0) if task.family else 0
        if task.family:
            family_seen[task.family] = occ + 1

        rows.append(
            {
                "task_id": task.task_id,
                "category": task.category,
                "tier": task.complexity_tier,
                "family": task.family,
                "occurrence": occ,
                "success": has_final and not failed,
                "escalated": (done or {}).get("escalations", 0) > 0,
                "cost_usd": trace.total_cost_usd,
                "tokens": trace.total_tokens,
                "latency_ms": trace.duration_ms,
                "plan_tokens": _plan_tokens(trace),
                "recalled": recall is not None,
                "recall_score": (recall["hits"][0]["score"] if recall else 0.0),
            }
        )

    return {
        "tasks": len(rows),
        "overall": _summary(rows),
        "by_category": _grouped(rows, "category"),
        "by_tier": _grouped(rows, "tier"),
        "memory": _memory_result(rows),
    }


def _summary(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return {
        "success_rate": round(mean(r["success"] for r in rows), 3),
        "escalation_rate": round(mean(r["escalated"] for r in rows), 3),
        "avg_cost_usd": round(mean(r["cost_usd"] for r in rows), 6),
        "avg_latency_ms": round(mean(r["latency_ms"] for r in rows), 2),
        "total_cost_usd": round(sum(r["cost_usd"] for r in rows), 6),
    }


def _grouped(rows: list[dict], key: str) -> dict:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r[key], []).append(r)
    return {k: {"n": len(v), **_summary(v)} for k, v in sorted(groups.items())}


def _memory_result(rows: list[dict]) -> dict:
    """The 'memory improves planning' result, with numbers."""
    fam_rows = [r for r in rows if r["family"]]
    first = [r for r in fam_rows if r["occurrence"] == 0]
    repeats = [r for r in fam_rows if r["occurrence"] > 0]
    return {
        "family_tasks": len(fam_rows),
        "first_occurrence_recall_rate": round(mean(r["recalled"] for r in first), 3) if first else 0.0,
        "repeat_occurrence_recall_rate": round(mean(r["recalled"] for r in repeats), 3) if repeats else 0.0,
        "avg_recall_score_on_repeats": round(mean(r["recall_score"] for r in repeats), 3) if repeats else 0.0,
    }
