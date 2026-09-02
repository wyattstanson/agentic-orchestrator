"""A database-backed trace store (same interface as the file TraceStore)."""

from __future__ import annotations

from app.observability.trace import Trace

from .base import session
from .models import TraceRow


class SqlTraceStore:
    def save(self, trace: Trace) -> None:
        s = session()
        try:
            payload = {
                "request": trace.request,
                "created_at": trace.created_at,
                "total_cost_usd": trace.total_cost_usd,
                "total_tokens": trace.total_tokens,
                "duration_ms": trace.duration_ms,
                "tool_calls": trace.tool_calls,
                "escalations": trace.escalations,
                "status": trace.status,
                "data": trace.model_dump_json(),
            }
            row = s.get(TraceRow, trace.task_id)
            if row is None:
                s.add(TraceRow(task_id=trace.task_id, **payload))
            else:
                for key, value in payload.items():
                    setattr(row, key, value)
            s.commit()
        finally:
            s.close()

    def get(self, task_id: str) -> Trace | None:
        s = session()
        try:
            row = s.get(TraceRow, task_id)
            return Trace.model_validate_json(row.data) if row else None
        finally:
            s.close()

    def _rows(self):
        s = session()
        try:
            return s.query(TraceRow).order_by(TraceRow.created_at.desc()).all()
        finally:
            s.close()

    def all(self) -> list[Trace]:
        return [Trace.model_validate_json(r.data) for r in self._rows()]

    def summaries(self) -> list[dict]:
        return [
            {
                "task_id": r.task_id,
                "request": r.request,
                "created_at": r.created_at,
                "duration_ms": r.duration_ms,
                "total_tokens": r.total_tokens,
                "total_cost_usd": r.total_cost_usd,
                "tool_calls": r.tool_calls,
                "escalations": r.escalations,
                "status": r.status,
            }
            for r in self._rows()
        ]
