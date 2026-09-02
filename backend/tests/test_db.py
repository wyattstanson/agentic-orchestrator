"""Persistence: tasks and traces survive in the database across store instances."""

from app.db import SqlTraceStore, init_db, repo
from app.observability import Tracer
from app.orchestration import Orchestrator


def test_task_roundtrip():
    init_db()
    repo.save_task(
        task_id="db-task-1",
        request="do a thing",
        status="done",
        final="the answer",
        cost_usd=0.01,
        tokens=100,
        tool_calls=2,
        escalations=0,
        subtasks=3,
        duration_ms=42.0,
        created_at=1000.0,
    )
    tasks = repo.list_tasks()
    ids = [t["task_id"] for t in tasks]
    assert "db-task-1" in ids


def test_trace_store_persists():
    store = SqlTraceStore()
    t = Tracer()
    t.reset("db-trace-1", "req")
    span = t.start("plan", agent="supervisor")
    t.record_usage("llama-3.1-8b-instant", 100, 50)
    t.end(span)
    store.save(t.finalize())

    # A fresh store instance reads it back from the DB (survives "restart").
    got = SqlTraceStore().get("db-trace-1")
    assert got is not None and got.task_id == "db-trace-1"
    assert got.total_tokens == 150
    assert any(s["task_id"] == "db-trace-1" for s in SqlTraceStore().summaries())


def test_stream_run_persists_task_and_trace_to_db():
    orch = Orchestrator()  # echo
    events = list(orch.stream_run("Reconcile a ledger and flag discrepancies"))
    task_id = next(e["task_id"] for e in events if e["type"] == "task_started")

    # Task record persisted...
    assert any(t["task_id"] == task_id for t in repo.list_tasks())
    # ...and its trace is in the DB, readable by a fresh store.
    assert SqlTraceStore().get(task_id) is not None
