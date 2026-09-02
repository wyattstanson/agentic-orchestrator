"""End-to-end orchestration via stream_run (no langgraph needed)."""

from app.memory import HashingEmbedder, LocalLongTermMemory
from app.orchestration import Orchestrator

from .helpers import RoleProvider

PLAN = (
    '{"task_id":"t1","request":"do X","rationale":"r",'
    '"subtasks":[{"id":"s1","description":"gather","specialist":"research",'
    '"inputs":[],"depends_on":[],"expected_output":"notes","complexity":"low"}]}'
)


def _events(provider) -> list[dict]:
    return list(Orchestrator(provider=provider).stream_run("do X"))


def test_stream_run_happy_path():
    provider = RoleProvider(
        plan=PLAN,
        specialist='{"final":"a solid answer","tool":null,"args":{}}',
        review='{"score":0.9,"passed":true,"feedback":"","rubric_scores":{}}',
    )
    events = _events(provider)
    types = [e["type"] for e in events]

    assert "plan" in types and "final" in types and "done" in types
    assert "escalation" not in types
    done = next(e for e in events if e["type"] == "subtask_done")
    assert done["status"] == "done"


def test_stream_run_escalates_on_repeated_rejection():
    provider = RoleProvider(
        plan=PLAN,
        specialist='{"final":"weak answer","tool":null,"args":{}}',
        review='{"score":0.2,"passed":false,"feedback":"insufficient","rubric_scores":{}}',
    )
    events = _events(provider)
    types = [e["type"] for e in events]

    assert "escalation" in types
    done = next(e for e in events if e["type"] == "subtask_done")
    assert done["status"] == "failed"
    # Two attempts were made before escalating.
    assert done["attempts"] == 2


def test_memory_is_recalled_on_a_similar_second_task(tmp_path):
    store = LocalLongTermMemory(HashingEmbedder(), tmp_path / "mem.json")
    provider = RoleProvider(
        plan=PLAN,
        specialist='{"final":"ok","tool":null,"args":{}}',
        review='{"score":0.9,"passed":true,"feedback":"","rubric_scores":{}}',
    )

    first = list(
        Orchestrator(provider=provider, longterm=store).stream_run(
            "Compare three vendors pricing and flag hidden fees"
        )
    )
    # Nothing to recall on the very first run.
    assert not any(e["type"] == "memory_recall" for e in first)

    second = list(
        Orchestrator(provider=provider, longterm=store).stream_run(
            "Compare vendors pricing and flag hidden fees"
        )
    )
    recalls = [e for e in second if e["type"] == "memory_recall"]
    assert recalls and recalls[0]["hits"]
