"""Persist traces so the explorer, analytics, and replay can read past runs."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import get_settings

from .trace import Trace


class TraceStore:
    def __init__(self, directory: str | Path):
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self._dir / f"{task_id}.json"

    def save(self, trace: Trace) -> None:
        self._path(trace.task_id).write_text(
            trace.model_dump_json(), encoding="utf-8"
        )

    def get(self, task_id: str) -> Trace | None:
        p = self._path(task_id)
        if not p.exists():
            return None
        return Trace.model_validate_json(p.read_text(encoding="utf-8"))

    def all(self) -> list[Trace]:
        traces = []
        for p in self._dir.glob("*.json"):
            try:
                traces.append(Trace.model_validate_json(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return sorted(traces, key=lambda t: t.created_at, reverse=True)

    def summaries(self) -> list[dict]:
        return [
            {
                "task_id": t.task_id,
                "request": t.request,
                "created_at": t.created_at,
                "duration_ms": t.duration_ms,
                "total_tokens": t.total_tokens,
                "total_cost_usd": t.total_cost_usd,
                "tool_calls": t.tool_calls,
                "escalations": t.escalations,
                "status": t.status,
            }
            for t in self.all()
        ]


@lru_cache
def get_trace_store():
    """The active trace store. Database-backed by default; set STORE_BACKEND=file
    to fall back to JSON files."""
    if get_settings().store_backend == "file":
        return TraceStore(Path(get_settings().memory_dir) / "traces")
    from app.db import SqlTraceStore  # lazy: avoids importing sqlalchemy for file mode

    return SqlTraceStore()
