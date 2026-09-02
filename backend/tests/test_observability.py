"""Tracing: span tree, token/cost roll-up, persistence, and analytics."""

from app.observability import Tracer, TraceStore, aggregate, compute_cost
from app.orchestration import Orchestrator


def test_cost_pricing():
    c = compute_cost("llama-3.3-70b-versatile", 1000, 1000)
    assert c == round(0.00059 + 0.00079, 6)


def test_tracer_builds_tree_and_rolls_up_cost():
    t = Tracer()
    t.reset("task-1", "do something")
    plan = t.start("plan", agent="supervisor")
    t.record_usage("llama-3.1-8b-instant", 100, 50)
    t.end(plan)

    sub = t.start("subtask:s1", agent="research")
    t.record_usage("llama-3.1-8b-instant", 200, 100)
    t.tool_span("web_search", ok=True, latency_ms=12.0)
    t.end(sub)

    trace = t.finalize()
    assert len(trace.spans) == 2
    assert trace.tool_calls == 1
    assert trace.total_tokens == 450
    assert trace.total_cost_usd > 0


def test_trace_store_roundtrip(tmp_path):
    store = TraceStore(tmp_path / "traces")
    t = Tracer()
    t.reset("task-xyz", "req")
    s = t.start("plan", agent="supervisor")
    t.end(s)
    store.save(t.finalize())

    got = store.get("task-xyz")
    assert got is not None and got.task_id == "task-xyz"
    assert len(store.summaries()) == 1


def test_stream_run_persists_a_trace_and_analytics():
    orch = Orchestrator()  # echo provider
    events = list(orch.stream_run("Summarise a vendor contract's risks"))
    task_id = next(e["task_id"] for e in events if e["type"] == "task_started")

    trace = orch.trace_store.get(task_id)
    assert trace is not None
    names = [s.name for s in trace.spans]
    assert "plan" in names and "synthesize" in names
    assert any(s.name.startswith("subtask:") for s in trace.spans)
    assert trace.total_tokens > 0  # echo estimates tokens
    assert trace.duration_ms >= 0

    agg = aggregate(orch.trace_store)
    assert agg["tasks"] >= 1
    assert agg["avg_cost_usd"] >= 0
