"""Long-term semantic memory (master-build-prompt §3).

`LocalLongTermMemory` is a JSON-persisted brute-force cosine store — real
semantic recall, runs offline, no services. `ChromaLongTermMemory` is the same
interface over ChromaDB when it's installed and selected.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from .embedding import Embedder, cosine
from .records import MemoryRecord


def _text_of(r: MemoryRecord) -> str:
    return " ".join([r.request, r.summary, " ".join(r.facts)])


class LongTermMemory(ABC):
    @abstractmethod
    def add(self, record: MemoryRecord) -> str: ...

    @abstractmethod
    def query(self, text: str, *, k: int = 3, min_score: float = 0.15) -> list[tuple[MemoryRecord, float]]: ...

    @abstractmethod
    def all(self) -> list[MemoryRecord]: ...

    @abstractmethod
    def get(self, record_id: str) -> MemoryRecord | None: ...

    @abstractmethod
    def delete(self, record_id: str) -> bool: ...


class LocalLongTermMemory(LongTermMemory):
    def __init__(self, embedder: Embedder, path: str | Path):
        self._embedder = embedder
        self._path = Path(path)
        self._records: dict[str, MemoryRecord] = {}
        self._load()

    # -- persistence --------------------------------------------------------
    def _load(self) -> None:
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._records = {d["id"]: MemoryRecord(**d) for d in data}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps([r.model_dump() for r in self._records.values()]),
            encoding="utf-8",
        )

    # -- core ---------------------------------------------------------------
    def add(self, record: MemoryRecord) -> str:
        if not record.embedding:
            record.embedding = self._embedder.embed(_text_of(record))
        self._records[record.id] = record
        self._save()
        return record.id

    def query(self, text: str, *, k: int = 3, min_score: float = 0.15) -> list[tuple[MemoryRecord, float]]:
        q = self._embedder.embed(text)
        scored = [
            (r, cosine(q, r.embedding)) for r in self._records.values() if r.embedding
        ]
        scored.sort(key=lambda t: t[1], reverse=True)
        hits = [(r, s) for r, s in scored if s >= min_score][:k]
        for r, _ in hits:  # retrieval boosts importance
            r.touch()
        if hits:
            self._save()
        return hits

    def all(self) -> list[MemoryRecord]:
        return sorted(
            self._records.values(), key=lambda r: r.importance(), reverse=True
        )

    def get(self, record_id: str) -> MemoryRecord | None:
        return self._records.get(record_id)

    def delete(self, record_id: str) -> bool:
        existed = self._records.pop(record_id, None) is not None
        if existed:
            self._save()
        return existed

    # -- lifecycle ----------------------------------------------------------
    def consolidate(self, threshold: float = 0.93) -> int:
        """Merge near-duplicate memories into one; returns how many were merged."""
        records = list(self._records.values())
        merged = 0
        removed: set[str] = set()
        for i, a in enumerate(records):
            if a.id in removed:
                continue
            for b in records[i + 1 :]:
                if b.id in removed or not a.embedding or not b.embedding:
                    continue
                if cosine(a.embedding, b.embedding) >= threshold:
                    a.tools = sorted(set(a.tools) | set(b.tools))
                    a.facts = sorted(set(a.facts) | set(b.facts))
                    a.specialists = sorted(set(a.specialists) | set(b.specialists))
                    a.access_count += b.access_count
                    removed.add(b.id)
                    merged += 1
        for rid in removed:
            self._records.pop(rid, None)
        if merged:
            self._save()
        return merged

    def prune(self, min_importance: float = 0.05) -> int:
        """Drop stale, rarely-used memories."""
        stale = [r.id for r in self._records.values() if r.importance() < min_importance]
        for rid in stale:
            self._records.pop(rid, None)
        if stale:
            self._save()
        return len(stale)


class ChromaLongTermMemory(LongTermMemory):
    """Same interface backed by ChromaDB (used when configured + installed)."""

    def __init__(self, embedder: Embedder, path: str | Path):
        import chromadb

        self._embedder = embedder
        self._client = chromadb.PersistentClient(path=str(path))
        self._col = self._client.get_or_create_collection("memories")

    def add(self, record: MemoryRecord) -> str:
        if not record.embedding:
            record.embedding = self._embedder.embed(_text_of(record))
        self._col.upsert(
            ids=[record.id],
            embeddings=[record.embedding],
            documents=[record.request],
            metadatas=[{"record": record.model_dump_json()}],
        )
        return record.id

    def _decode(self, meta: dict) -> MemoryRecord:
        return MemoryRecord(**json.loads(meta["record"]))

    def query(self, text: str, *, k: int = 3, min_score: float = 0.15) -> list[tuple[MemoryRecord, float]]:
        res = self._col.query(
            query_embeddings=[self._embedder.embed(text)], n_results=k
        )
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        out: list[tuple[MemoryRecord, float]] = []
        for meta, dist in zip(metas, dists):
            score = 1.0 - float(dist)  # cosine distance -> similarity
            if score >= min_score:
                rec = self._decode(meta)
                rec.touch()
                self._col.update(ids=[rec.id], metadatas=[{"record": rec.model_dump_json()}])
                out.append((rec, score))
        return out

    def all(self) -> list[MemoryRecord]:
        res = self._col.get()
        recs = [self._decode(m) for m in (res.get("metadatas") or [])]
        return sorted(recs, key=lambda r: r.importance(), reverse=True)

    def get(self, record_id: str) -> MemoryRecord | None:
        res = self._col.get(ids=[record_id])
        metas = res.get("metadatas") or []
        return self._decode(metas[0]) if metas else None

    def delete(self, record_id: str) -> bool:
        self._col.delete(ids=[record_id])
        return True
