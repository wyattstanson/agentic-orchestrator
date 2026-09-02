"""FastAPI layer — exposes the orchestrator to the frontend.

Endpoints:
  GET  /health              liveness + which provider is active
  GET  /api/tools           the tool registry
  POST /api/tasks/stream    run a task, streaming progress as Server-Sent Events
"""

from __future__ import annotations

import json
from typing import Iterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import get_settings
from app.tools import build_default_registry

app = FastAPI(title="Orchestrator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    request: str
    approve_plan: bool = False


class ResolveBody(BaseModel):
    decision: str  # approve | reject | modify | take_over
    modified_output: str | None = None
    note: str | None = None


class ChatBody(BaseModel):
    question: str


@app.on_event("startup")
def _startup() -> None:
    from app.db import init_db

    init_db()


@app.get("/health")
def health() -> dict:
    s = get_settings()
    return {"ok": True, "provider": s.llm_provider}


@app.get("/api/tasks")
def tasks_list() -> list[dict]:
    from app.db import repo

    return repo.list_tasks()


@app.get("/api/tools")
def tools() -> list[dict]:
    registry = build_default_registry()
    return [spec.model_dump(mode="json") for spec in registry.specs()]


@app.get("/api/memory")
def memory_list() -> list[dict]:
    from app.memory import get_longterm_memory

    out = []
    for r in get_longterm_memory().all():
        d = r.model_dump(exclude={"embedding"})
        d["importance"] = r.importance()
        out.append(d)
    return out


@app.delete("/api/memory/{record_id}")
def memory_delete(record_id: str) -> dict:
    from app.memory import get_longterm_memory

    return {"ok": get_longterm_memory().delete(record_id)}


@app.post("/api/memory/maintain")
def memory_maintain() -> dict:
    from app.memory import get_longterm_memory

    store = get_longterm_memory()
    merged = store.consolidate() if hasattr(store, "consolidate") else 0
    pruned = store.prune() if hasattr(store, "prune") else 0
    return {"consolidated": merged, "pruned": pruned}


def _sse(events: Iterator[dict]) -> Iterator[str]:
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"


@app.post("/api/tasks/stream")
def run_task_stream(body: TaskRequest) -> StreamingResponse:
    # Imported here so the module loads even before langgraph is installed.
    from app.hitl import get_queue
    from app.orchestration import Orchestrator

    queue = get_queue()

    def resolver(req):  # persist the approval, then block on the human decision
        from app.db import repo

        repo.save_approval(
            id=req.id,
            task_id=req.task_id,
            subtask_id=req.subtask_id,
            level=req.level.value,
            trigger=req.trigger.value,
            reason=req.reason,
            created_at=req.created_at,
            data=req.model_dump_json(),
        )
        return queue.submit(req, timeout=1800)

    def gen() -> Iterator[str]:
        try:
            orch = Orchestrator(resolver=resolver)
            yield from _sse(
                orch.stream_run(body.request, approve_plan=body.approve_plan)
            )
        except Exception as exc:  # surface init/runtime errors to the client
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# -- human-in-the-loop approvals -------------------------------------------
@app.get("/api/approvals")
def approvals_pending() -> list[dict]:
    from app.hitl import get_queue

    return [r.model_dump() for r in get_queue().pending()]


@app.get("/api/approvals/{request_id}")
def approval_get(request_id: str) -> dict:
    from fastapi import HTTPException

    from app.hitl import get_queue

    req = get_queue().get(request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Unknown approval request")
    return req.model_dump()


@app.post("/api/approvals/{request_id}/resolve")
def approval_resolve(request_id: str, body: ResolveBody) -> dict:
    from app.hitl import Resolution, get_queue

    ok = get_queue().resolve(
        request_id,
        Resolution(
            decision=body.decision,  # type: ignore[arg-type]
            modified_output=body.modified_output,
            note=body.note,
        ),
    )
    if ok:
        from app.db import repo

        repo.resolve_approval(request_id, body.decision)
    return {"ok": ok}


@app.get("/api/traces")
def traces_list() -> list[dict]:
    from app.observability import get_trace_store

    return get_trace_store().summaries()


@app.get("/api/traces/{task_id}")
def trace_get(task_id: str) -> dict:
    from fastapi import HTTPException

    from app.observability import get_trace_store

    trace = get_trace_store().get(task_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Unknown trace")
    return trace.model_dump()


@app.get("/api/analytics")
def analytics() -> dict:
    from app.observability import aggregate, get_trace_store

    return aggregate(get_trace_store())


@app.get("/api/eval/report")
def eval_report() -> dict:
    from pathlib import Path

    p = Path(__file__).resolve().parents[2] / "eval" / "report.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


@app.post("/api/approvals/{request_id}/chat")
def approval_chat(request_id: str, body: ChatBody) -> dict:
    from fastapi import HTTPException

    from app.hitl import ChatTurn, answer_question, get_queue

    queue = get_queue()
    req = queue.get(request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Unknown approval request")
    queue.add_chat(request_id, ChatTurn(role="human", text=body.question))
    answer = answer_question(req, body.question)
    queue.add_chat(request_id, ChatTurn(role="agent", text=answer))
    return {"answer": answer, "chat": [t.model_dump() for t in req.chat]}
