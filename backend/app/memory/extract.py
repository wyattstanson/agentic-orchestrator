"""Distil a completed task into a long-term memory record."""

from __future__ import annotations

from app.models import Plan

from .records import MemoryRecord


def extract_memory(
    *,
    task_id: str,
    request: str,
    plan: Plan,
    tools_used: list[str],
    success: bool,
    facts: list[str] | None = None,
) -> MemoryRecord:
    specialists = sorted({s.specialist.value for s in plan.subtasks})
    summary = plan.rationale or (
        f"Solved with {len(plan.subtasks)} subtasks across "
        f"{', '.join(specialists) or 'no'} specialists."
    )
    return MemoryRecord(
        task_id=task_id,
        request=request,
        summary=summary,
        specialists=specialists,
        tools=sorted(set(tools_used)),
        facts=facts or [],
        success=success,
    )
