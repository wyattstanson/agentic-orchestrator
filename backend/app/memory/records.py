"""What the system remembers across tasks."""

from __future__ import annotations

import time
import uuid

from pydantic import BaseModel, Field


class MemoryRecord(BaseModel):
    """A distilled memory of one completed task (master-build-prompt §3)."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    task_id: str
    request: str
    summary: str = Field(default="", description="Approach that worked.")
    specialists: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list, description="Domain facts learned.")
    success: bool = True

    created_at: float = Field(default_factory=time.time)
    last_accessed: float = Field(default_factory=time.time)
    access_count: int = 0
    # Persisted so a store can rank without recomputing embeddings.
    embedding: list[float] = Field(default_factory=list)

    def importance(self, *, half_life_days: float = 14.0) -> float:
        """Frequently-retrieved, recent memories rank higher; stale ones decay."""
        age_days = (time.time() - self.last_accessed) / 86_400
        recency = 0.5 ** (age_days / half_life_days)
        frequency = 1.0 + self.access_count
        return round(frequency * recency, 4)

    def touch(self) -> None:
        self.last_accessed = time.time()
        self.access_count += 1
