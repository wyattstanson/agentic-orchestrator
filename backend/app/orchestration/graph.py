"""The orchestration state machine: intake → plan → execute → synthesize.

Execution respects the plan's dependency layers, reviews each specialist's
output, retries once on rejection, and escalates on a second rejection.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Iterator

from app.agents import Reviewer, Specialist, Supervisor
from app.config import get_settings
from app.hitl import ApprovalRequest, Resolution
from app.llm import LLMProvider, get_provider
from app.memory import (
    LongTermMemory,
    WorkingMemory,
    extract_memory,
    get_longterm_memory,
    get_working_memory,
)
from app.models import DEFAULT_LEVEL, Escalation, OrchestrationState, new_state
from app.models.enums import EscalationLevel, EscalationTrigger
from app.models.state import SubtaskRun
from app.observability import Tracer, TracingProvider, get_trace_store
from app.tools import ToolRegistry, build_default_registry

Resolver = Callable[[ApprovalRequest], Resolution]


def _approval_public(req: ApprovalRequest) -> dict:
    """Trim an approval request to what the client needs for the event."""
    return {
        "id": req.id,
        "task_id": req.task_id,
        "subtask_id": req.subtask_id,
        "level": req.level.value,
        "trigger": req.trigger.value,
        "reason": req.reason,
        "proposed_action": req.proposed_action,
        "agent_reasoning": req.agent_reasoning,
    }


class Orchestrator:
    def __init__(
        self,
        provider: LLMProvider | None = None,
        registry: ToolRegistry | None = None,
        working: WorkingMemory | None = None,
        longterm: LongTermMemory | None = None,
        resolver: Resolver | None = None,
    ):
        settings = get_settings()
        provider = provider or get_provider()
        self.registry = registry or build_default_registry()
        self.working = working or get_working_memory()
        self.longterm = longterm or get_longterm_memory()
        # When set, escalations pause the run and block on a human decision.
        self.resolver = resolver
        # Tracing: agents call through a wrapper that attributes tokens + cost
        # to the currently-open span.
        self.tracer = Tracer()
        self.trace_store = get_trace_store()
        traced = TracingProvider(provider, self.tracer)
        self.supervisor = Supervisor(traced, settings.llm_model_planner)
        self.specialist = Specialist(traced, settings.llm_model_specialist)
        self.reviewer = Reviewer(traced, settings.llm_model_reviewer)
        # Built lazily so stream_run() and tests don't require langgraph.
        self._app = None

    # -- memory helpers -----------------------------------------------------
    def _recall(self, request: str) -> tuple[list[str], list[dict]]:
        hits = self.longterm.query(request, k=3)
        hints = [f"{r.request} — {r.summary}" for r, _ in hits]
        summary = [{"request": r.request, "score": round(s, 3)} for r, s in hits]
        return hints, summary

    def _remember(self, state: OrchestrationState) -> None:
        plan = state.get("plan")
        if plan is None:
            return
        record = extract_memory(
            task_id=state["task_id"],
            request=state["request"],
            plan=plan,
            tools_used=[inv.tool for inv in self.registry.log],
            success=not state.get("errors"),
        )
        self.longterm.add(record)
        self.working.clear(state["task_id"])

    # -- nodes --------------------------------------------------------------
    def _plan(self, state: OrchestrationState) -> dict:
        hints, _ = self._recall(state["request"])
        plan = self.supervisor.decompose(
            state["request"], task_id=state["task_id"], memory_hints=hints or None
        )
        runs = {s.id: SubtaskRun(subtask_id=s.id) for s in plan.subtasks}
        self.working.set(state["task_id"], "plan", plan.model_dump(mode="json"))
        return {"plan": plan, "runs": runs}

    def _execute(self, state: OrchestrationState) -> dict:
        plan = state["plan"]
        runs = state["runs"]
        completed: dict[str, str] = {}
        escalations: list[Escalation] = []
        errors: list[str] = []
        assert plan is not None

        for layer in plan.execution_order():
            for sid in layer:
                sub = next(s for s in plan.subtasks if s.id == sid)
                context = {d: completed.get(d, "") for d in sub.depends_on}
                run = runs[sid]
                run.status = "running"
                review = None
                output = ""
                for _ in range(2):  # one retry on rejection
                    run.attempts += 1
                    output, reasoning = self.specialist.run(
                        sub, context, self.registry
                    )
                    run.output, run.reasoning = output, reasoning
                    review = self.reviewer.review(sub, output)
                    run.review = review
                    if review.passed:
                        break

                completed[sid] = output
                if review and review.passed:
                    run.status = "done"
                else:
                    run.status = "failed"
                    errors.append(f"{sid} failed review after {run.attempts} attempts")
                    trigger = EscalationTrigger.REVIEW_REJECTED
                    escalations.append(
                        Escalation(
                            task_id=state["task_id"],
                            subtask_id=sid,
                            trigger=trigger,
                            level=DEFAULT_LEVEL[trigger],
                            reason=f"Reviewer rejected '{sid}' twice.",
                            proposed_action=output[:400],
                            agent_reasoning=(review.feedback if review else ""),
                        )
                    )
        return {
            "runs": runs,
            "completed": completed,
            "escalations": escalations,
            "errors": errors,
        }

    def _synthesize(self, state: OrchestrationState) -> dict:
        final = self.supervisor.synthesize(state["request"], state["completed"])
        self._remember(state)
        return {"final": final}

    # -- graph --------------------------------------------------------------
    def _build(self):
        from langgraph.graph import END, START, StateGraph

        g = StateGraph(OrchestrationState)
        g.add_node("plan", self._plan)
        g.add_node("execute", self._execute)
        g.add_node("synthesize", self._synthesize)
        g.add_edge(START, "plan")
        g.add_edge("plan", "execute")
        g.add_edge("execute", "synthesize")
        g.add_edge("synthesize", END)
        return g.compile()

    # -- public -------------------------------------------------------------
    def run(self, request: str, *, task_id: str | None = None) -> OrchestrationState:
        if self._app is None:
            self._app = self._build()
        task_id = task_id or f"task-{uuid.uuid4().hex[:8]}"
        state = new_state(task_id, request)
        return self._app.invoke(state)  # type: ignore[return-value]

    def stream_run(
        self,
        request: str,
        *,
        task_id: str | None = None,
        approve_plan: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """Run a task and yield progress events (drives the live UI / SSE).

        Mirrors the graph's plan → execute → synthesize flow, emitting an event
        at every boundary so the frontend can animate the constellation and
        stream reasoning as it happens.
        """
        task_id = task_id or f"task-{uuid.uuid4().hex[:8]}"
        self.tracer.reset(task_id, request)
        yield {"type": "task_started", "task_id": task_id, "request": request}

        # Recall similar past tasks — the "memory improves planning" moment.
        rspan = self.tracer.start("recall", agent="memory")
        hints, recalled = self._recall(request)
        rspan.attributes["hits"] = len(recalled)
        self.tracer.end(rspan)
        if recalled:
            yield {"type": "memory_recall", "hits": recalled}

        # Plan
        yield {"type": "agent_active", "agent": "supervisor"}
        pspan = self.tracer.start("plan", agent="supervisor")
        plan = self.supervisor.decompose(
            request, task_id=task_id, memory_hints=hints or None
        )
        pspan.attributes["subtasks"] = len(plan.subtasks)
        self.tracer.end(pspan)
        self.working.set(task_id, "plan", plan.model_dump(mode="json"))
        yield {"type": "plan", "plan": plan.model_dump(mode="json")}

        # Optional plan-level approval (APPROVE_PLAN) before any work starts.
        if approve_plan and self.resolver is not None:
            req = ApprovalRequest(
                task_id=task_id,
                level=EscalationLevel.APPROVE_PLAN,
                trigger=EscalationTrigger.USER_REQUESTED,
                reason="Approve the plan before execution begins.",
                proposed_action="\n".join(
                    f"{s.id} [{s.specialist.value}] {s.description}"
                    for s in plan.subtasks
                ),
                agent_reasoning=plan.rationale,
                context={"subtasks": len(plan.subtasks)},
            )
            yield {"type": "awaiting_approval", "request": _approval_public(req)}
            resolution = self.resolver(req)
            yield {
                "type": "approval_resolved",
                "id": req.id,
                "decision": resolution.decision,
            }
            self.tracer.mark_escalation("approve_plan")
            if resolution.decision == "reject":
                self.trace_store.save(self.tracer.finalize(status="aborted"))
                yield {"type": "aborted", "reason": "Plan was rejected."}
                return

        completed: dict[str, str] = {}
        n_escalations = 0
        for layer in plan.execution_order():
            for sid in layer:
                sub = next(s for s in plan.subtasks if s.id == sid)
                context = {d: completed.get(d, "") for d in sub.depends_on}
                yield {
                    "type": "subtask_started",
                    "id": sid,
                    "specialist": sub.specialist.value,
                    "description": sub.description,
                }
                yield {"type": "agent_active", "agent": sub.specialist.value}

                sub_span = self.tracer.start(
                    f"subtask:{sid}",
                    agent=sub.specialist.value,
                    description=sub.description[:100],
                )
                review = None
                output = ""
                attempts = 0
                for _ in range(2):
                    attempts += 1
                    log_before = len(self.registry.log)
                    output, _reasoning = self.specialist.run(
                        sub, context, self.registry
                    )
                    for inv in self.registry.log[log_before:]:
                        self.tracer.tool_span(
                            inv.tool,
                            ok=inv.result.ok,
                            latency_ms=inv.result.latency_ms,
                            error=inv.result.error,
                        )
                        yield {
                            "type": "tool_call",
                            "id": sid,
                            "tool": inv.tool,
                            "ok": inv.result.ok,
                            "latency_ms": inv.result.latency_ms,
                        }
                        spec = self.registry.get(inv.tool)
                        if spec and spec.sensitive:
                            n_escalations += 1
                            yield {
                                "type": "escalation",
                                "id": sid,
                                "level": "approve_action",
                                "reason": f"Sensitive tool '{inv.tool}' requires approval.",
                            }
                    yield {"type": "subtask_output", "id": sid, "output": output}

                    yield {"type": "agent_active", "agent": "reviewer"}
                    rev_span = self.tracer.start("review", agent="reviewer")
                    review = self.reviewer.review(sub, output)
                    rev_span.attributes["score"] = review.score
                    self.tracer.end(
                        rev_span, status="ok" if review.passed else "error"
                    )
                    yield {
                        "type": "review",
                        "id": sid,
                        "passed": review.passed,
                        "score": review.score,
                        "feedback": review.feedback,
                    }
                    if review.passed:
                        break
                    yield {"type": "agent_active", "agent": sub.specialist.value}

                passed = bool(review and review.passed)
                if not passed and self.resolver is not None:
                    # Pause: package context and block on a human decision.
                    req = ApprovalRequest(
                        task_id=task_id,
                        subtask_id=sid,
                        level=DEFAULT_LEVEL[EscalationTrigger.REVIEW_REJECTED],
                        trigger=EscalationTrigger.REVIEW_REJECTED,
                        reason=f"Reviewer rejected '{sid}' after {attempts} attempts.",
                        proposed_action=output[:800],
                        agent_reasoning=(review.feedback if review else ""),
                        context={"subtask": sub.description},
                    )
                    yield {"type": "awaiting_approval", "request": _approval_public(req)}
                    resolution = self.resolver(req)
                    yield {
                        "type": "approval_resolved",
                        "id": req.id,
                        "decision": resolution.decision,
                    }
                    if resolution.decision in ("modify", "take_over"):
                        output = resolution.modified_output or output
                        status = "done"
                    elif resolution.decision == "approve":
                        status = "done"
                    else:  # reject
                        status = "failed"
                        n_escalations += 1
                elif not passed:
                    status = "failed"
                    n_escalations += 1
                    yield {
                        "type": "escalation",
                        "id": sid,
                        "level": "approve_action",
                        "reason": f"Reviewer rejected '{sid}' twice.",
                    }
                else:
                    status = "done"

                if not passed:
                    self.tracer.mark_escalation("approve_action")
                self.tracer.end(sub_span, status="ok" if status == "done" else "error")
                completed[sid] = output
                yield {
                    "type": "subtask_done",
                    "id": sid,
                    "status": status,
                    "attempts": attempts,
                }

        # Synthesis
        yield {"type": "agent_active", "agent": "supervisor"}
        syn_span = self.tracer.start("synthesize", agent="supervisor")
        final = self.supervisor.synthesize(request, completed)
        self.tracer.end(syn_span)
        yield {"type": "final", "final": final}

        # Persist what was learned for next time.
        record = extract_memory(
            task_id=task_id,
            request=request,
            plan=plan,
            tools_used=[inv.tool for inv in self.registry.log],
            success=(n_escalations == 0),
        )
        self.longterm.add(record)
        self.working.clear(task_id)

        trace = self.tracer.finalize(status="ok" if n_escalations == 0 else "error")
        self.trace_store.save(trace)

        from app.db import repo  # persist the canonical task record

        repo.save_task(
            task_id=task_id,
            request=request,
            status="escalated" if n_escalations else "done",
            final=final,
            cost_usd=trace.total_cost_usd,
            tokens=trace.total_tokens,
            tool_calls=trace.tool_calls,
            escalations=n_escalations,
            subtasks=len(plan.subtasks),
            duration_ms=trace.duration_ms,
            created_at=trace.created_at,
        )

        yield {
            "type": "done",
            "task_id": task_id,
            "subtasks": len(plan.subtasks),
            "tool_calls": trace.tool_calls,
            "escalations": n_escalations,
            "cost_usd": trace.total_cost_usd,
            "tokens": trace.total_tokens,
        }
