"""Schema for one structured agentic task (master-build-prompt §6)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgenticTask(BaseModel):
    task_id: str
    category: str
    request: str
    expected_subtasks: list[str] = Field(default_factory=list)
    expected_tools: list[str] = Field(default_factory=list)
    complexity_tier: str = "medium"  # low | medium | high
    should_escalate: bool = False
    reviewer_rubric: list[str] = Field(default_factory=list)
    known_failure_modes: list[str] = Field(default_factory=list)
    # Tasks sharing a family are deliberately similar — used to prove that the
    # second/third occurrence recalls memory from the first.
    family: str | None = None
