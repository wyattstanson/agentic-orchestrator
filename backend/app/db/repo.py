"""Data-access helpers for the persistent agentic-stream state."""

from __future__ import annotations

from typing import Any

from .base import session
from .models import ApprovalRow, TaskRow


def save_task(**fields: Any) -> None:
    """Upsert a task run record."""
    s = session()
    try:
        row = s.get(TaskRow, fields["task_id"])
        if row is None:
            s.add(TaskRow(**fields))
        else:
            for key, value in fields.items():
                setattr(row, key, value)
        s.commit()
    finally:
        s.close()


def list_tasks(limit: int = 50) -> list[dict]:
    s = session()
    try:
        rows = (
            s.query(TaskRow).order_by(TaskRow.created_at.desc()).limit(limit).all()
        )
        return [
            {
                "task_id": r.task_id,
                "request": r.request,
                "status": r.status,
                "cost_usd": r.cost_usd,
                "tokens": r.tokens,
                "tool_calls": r.tool_calls,
                "escalations": r.escalations,
                "subtasks": r.subtasks,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    finally:
        s.close()


def save_approval(
    *,
    id: str,
    task_id: str,
    subtask_id: str | None,
    level: str,
    trigger: str,
    reason: str,
    created_at: float,
    data: str,
) -> None:
    s = session()
    try:
        if s.get(ApprovalRow, id) is None:
            s.add(
                ApprovalRow(
                    id=id,
                    task_id=task_id,
                    subtask_id=subtask_id,
                    level=level,
                    trigger=trigger,
                    reason=reason,
                    status="pending",
                    created_at=created_at,
                    data=data,
                )
            )
            s.commit()
    finally:
        s.close()


def resolve_approval(id: str, decision: str) -> None:
    s = session()
    try:
        row = s.get(ApprovalRow, id)
        if row is not None:
            row.status = "resolved"
            row.decision = decision
            s.commit()
    finally:
        s.close()
