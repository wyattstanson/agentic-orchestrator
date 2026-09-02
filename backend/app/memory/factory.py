"""Select memory backends from configuration (with offline-safe fallbacks)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.config import get_settings

from .embedding import HashingEmbedder
from .longterm import ChromaLongTermMemory, LocalLongTermMemory, LongTermMemory
from .working import InMemoryWorkingMemory, RedisWorkingMemory, WorkingMemory


@lru_cache
def get_working_memory() -> WorkingMemory:
    s = get_settings()
    if s.working_memory == "redis" and s.redis_url:
        try:
            return RedisWorkingMemory(s.redis_url)
        except Exception:
            pass  # fall back to in-process
    return InMemoryWorkingMemory()


@lru_cache
def get_longterm_memory() -> LongTermMemory:
    s = get_settings()
    embedder = HashingEmbedder()
    base = Path(s.memory_dir)
    if s.memory_backend == "chroma":
        try:
            return ChromaLongTermMemory(embedder, base / "chroma")
        except Exception:
            pass  # fall back to the local store
    return LocalLongTermMemory(embedder, base / "memories.json")
