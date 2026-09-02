"""A hierarchical execution trace (OpenTelemetry-style spans).

Every task run produces a `Trace`: a tree of `Span`s for planning, each
specialist, its tool calls, reviewer evaluations, and synthesis — each carrying
latency, tokens, cost, and status. This is the first-class object the trace
explorer, cost tracking, and replay all read.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from .cost import compute_cost


class Span(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str
    agent: str = ""
    status: str = "ok"  # ok | error | paused
    started: float = Field(default_factory=time.time)
    ended: float | None = None
    duration_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    attributes: dict[str, Any] = Field(default_factory=dict)
    children: list["Span"] = Field(default_factory=list)


class Trace(BaseModel):
    task_id: str
    request: str = ""
    created_at: float = Field(default_factory=time.time)
    spans: list[Span] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    duration_ms: float = 0.0
    tool_calls: int = 0
    escalations: int = 0
    status: str = "ok"


class Tracer:
    """Builds a Trace by starting/ending spans; tokens attribute to the open one."""

    def __init__(self) -> None:
        self.trace = Trace(task_id="")
        self._stack: list[Span] = []

    def reset(self, task_id: str, request: str) -> None:
        self.trace = Trace(task_id=task_id, request=request)
        self._stack = []

    def start(self, name: str, *, agent: str = "", **attrs: Any) -> Span:
        span = Span(name=name, agent=agent, attributes=dict(attrs))
        (self._stack[-1].children if self._stack else self.trace.spans).append(span)
        self._stack.append(span)
        return span

    def end(self, span: Span, *, status: str = "ok") -> None:
        span.ended = time.time()
        span.duration_ms = round((span.ended - span.started) * 1000, 2)
        span.status = status
        if self._stack and self._stack[-1] is span:
            self._stack.pop()

    def record_usage(self, model: str, tokens_in: int, tokens_out: int) -> None:
        if not self._stack:
            return
        top = self._stack[-1]
        top.tokens_in += tokens_in
        top.tokens_out += tokens_out
        top.cost_usd = round(top.cost_usd + compute_cost(model, tokens_in, tokens_out), 6)

    def tool_span(self, tool: str, *, ok: bool, latency_ms: float, error: str | None = None) -> None:
        parent = self._stack[-1].children if self._stack else self.trace.spans
        now = time.time()
        parent.append(
            Span(
                name=f"tool:{tool}",
                agent="tool",
                status="ok" if ok else "error",
                started=now,
                ended=now,
                duration_ms=latency_ms,
                attributes={"error": error} if error else {},
            )
        )
        self.trace.tool_calls += 1

    def mark_escalation(self, level: str) -> None:
        self.trace.escalations += 1
        if self._stack:
            self._stack[-1].attributes["escalation"] = level
            self._stack[-1].status = "paused"

    def finalize(self, *, status: str = "ok") -> Trace:
        def walk(span: Span) -> tuple[int, float]:
            tok = span.tokens_in + span.tokens_out
            cost = span.cost_usd
            for child in span.children:
                ctok, ccost = walk(child)
                tok += ctok
                cost += ccost
            return tok, cost

        total_tok = 0
        total_cost = 0.0
        for root in self.trace.spans:
            t, c = walk(root)
            total_tok += t
            total_cost += c
        self.trace.total_tokens = total_tok
        self.trace.total_cost_usd = round(total_cost, 6)
        self.trace.duration_ms = round((time.time() - self.trace.created_at) * 1000, 2)
        self.trace.status = status
        return self.trace
