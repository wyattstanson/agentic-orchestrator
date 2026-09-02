"""Reviewer output schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewResult(BaseModel):
    """The reviewer's structured verdict on a specialist's output."""

    score: float = Field(ge=0.0, le=1.0, description="Overall quality, 0..1.")
    passed: bool
    feedback: str = Field(description="Actionable feedback if not passed.")
    rubric_scores: dict[str, bool] = Field(
        default_factory=dict,
        description="Per-criterion pass/fail keyed by the rubric item.",
    )
