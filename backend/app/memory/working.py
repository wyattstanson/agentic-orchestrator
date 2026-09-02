"""Working memory — scoped to a single task, cleared on completion.

Default is in-process; Redis is used when REDIS_URL is set and `redis` is
installed. Both implement the same interface.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any


class WorkingMemory(ABC):
    @abstractmethod
    def set(self, task_id: str, key: str, value: Any) -> None: ...

    @abstractmethod
    def get(self, task_id: str, key: str) -> Any | None: ...

    @abstractmethod
    def append(self, task_id: str, key: str, item: Any) -> None: ...

    @abstractmethod
    def snapshot(self, task_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def clear(self, task_id: str) -> None: ...


class InMemoryWorkingMemory(WorkingMemory):
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def set(self, task_id: str, key: str, value: Any) -> None:
        self._store.setdefault(task_id, {})[key] = value

    def get(self, task_id: str, key: str) -> Any | None:
        return self._store.get(task_id, {}).get(key)

    def append(self, task_id: str, key: str, item: Any) -> None:
        bucket = self._store.setdefault(task_id, {})
        bucket.setdefault(key, [])
        if not isinstance(bucket[key], list):
            bucket[key] = [bucket[key]]
        bucket[key].append(item)

    def snapshot(self, task_id: str) -> dict[str, Any]:
        return dict(self._store.get(task_id, {}))

    def clear(self, task_id: str) -> None:
        self._store.pop(task_id, None)


class RedisWorkingMemory(WorkingMemory):
    """Task-scoped state in a Redis hash with a TTL. Values are JSON-encoded."""

    def __init__(self, url: str, ttl_seconds: int = 3600):
        import redis  # lazy: only needed when Redis is selected

        self._r = redis.from_url(url, decode_responses=True)
        self._ttl = ttl_seconds

    def _key(self, task_id: str) -> str:
        return f"wm:{task_id}"

    def set(self, task_id: str, key: str, value: Any) -> None:
        self._r.hset(self._key(task_id), key, json.dumps(value))
        self._r.expire(self._key(task_id), self._ttl)

    def get(self, task_id: str, key: str) -> Any | None:
        raw = self._r.hget(self._key(task_id), key)
        return json.loads(raw) if raw is not None else None

    def append(self, task_id: str, key: str, item: Any) -> None:
        current = self.get(task_id, key)
        current = current if isinstance(current, list) else ([] if current is None else [current])
        current.append(item)
        self.set(task_id, key, current)

    def snapshot(self, task_id: str) -> dict[str, Any]:
        raw = self._r.hgetall(self._key(task_id))
        return {k: json.loads(v) for k, v in raw.items()}

    def clear(self, task_id: str) -> None:
        self._r.delete(self._key(task_id))
