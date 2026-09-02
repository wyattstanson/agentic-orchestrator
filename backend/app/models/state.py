"""The orchestration state carried through the LangGraph state machine."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field

from .escalation import Escalation
from .plan import Plan
from .review import ReviewResult


class SubtaskRun(BaseModel):
    subtask_id: str
    status: str = "pending"  # pending | running | reviewed | failed | done
    attempts: int = 0
    output: str = ""
    reasoning: str = ""
    review: ReviewResult | None = None


class OrchestrationState(TypedDict, total=False):
    """Working state for a single task run (LangGraph channel dict)."""

    task_id: str
    request: str
    plan: Plan | None
    runs: dict[str, SubtaskRun]
    completed: dict[str, str]  # subtask_id -> output
    errors: list[str]
    escalations: list[Escalation]
    paused: bool
    final: str | None


def new_state(task_id: str, request: str) -> OrchestrationState:
    return OrchestrationState(
        task_id=task_id,
        request=request,
        plan=None,
        runs={},
        completed={},
        errors=[],
        escalations=[],
        paused=False,
        final=None,
    )
