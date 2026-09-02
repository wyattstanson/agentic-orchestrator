"""Memory: embeddings, the vector store, lifecycle, extraction, and recall."""

from app.memory import HashingEmbedder, LocalLongTermMemory, MemoryRecord, cosine, extract_memory
from app.models import Plan, Subtask
from app.models.enums import SpecialistRole


def _store(tmp_path) -> LocalLongTermMemory:
    return LocalLongTermMemory(HashingEmbedder(), tmp_path / "mem.json")


def _rec(request: str, **kw) -> MemoryRecord:
    return MemoryRecord(task_id="t", request=request, **kw)


def test_embedding_similar_beats_dissimilar():
    emb = HashingEmbedder()
    a = emb.embed("compare vendor pricing and hidden fees")
    b = emb.embed("compare three vendors pricing and flag hidden fees")
    c = emb.embed("debug a flaky database migration script")
    assert cosine(a, b) > cosine(a, c)


def test_add_query_delete(tmp_path):
    store = _store(tmp_path)
    rid = store.add(_rec("compare vendor pricing and flag hidden fees"))
    store.add(_rec("summarise a legal contract's risks"))

    hits = store.query("compare three vendors pricing hidden fees", k=3)
    assert hits and hits[0][0].id == rid  # most similar first

    assert store.delete(rid) is True
    assert store.get(rid) is None


def test_query_boosts_importance(tmp_path):
    store = _store(tmp_path)
    rid = store.add(_rec("reconcile the quarterly ledger"))
    before = store.get(rid).importance()
    store.query("reconcile quarterly ledger", k=1)
    after = store.get(rid).importance()
    assert store.get(rid).access_count == 1
    assert after >= before


def test_consolidate_merges_near_duplicates(tmp_path):
    store = _store(tmp_path)
    store.add(_rec("compare vendor pricing and flag hidden fees", tools=["web_search"]))
    store.add(_rec("compare vendor pricing and flag hidden fees", tools=["file_write"]))
    merged = store.consolidate(threshold=0.9)
    assert merged == 1
    remaining = store.all()
    assert len(remaining) == 1
    assert set(remaining[0].tools) == {"web_search", "file_write"}


def test_extract_memory_from_plan():
    plan = Plan(
        task_id="t1",
        request="do X",
        subtasks=[
            Subtask(id="s1", description="a", specialist=SpecialistRole.RESEARCH, expected_output="x"),
            Subtask(id="s2", description="b", specialist=SpecialistRole.WRITING, depends_on=["s1"], expected_output="y"),
        ],
    )
    rec = extract_memory(task_id="t1", request="do X", plan=plan, tools_used=["web_search", "web_search"], success=True)
    assert rec.specialists == ["research", "writing"]
    assert rec.tools == ["web_search"]  # de-duplicated
    assert rec.success is True
