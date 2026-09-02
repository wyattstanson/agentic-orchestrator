"""Reviewer — grades specialist output against a rubric before it goes up."""

from __future__ import annotations

from app.llm import structured
from app.models import ReviewResult, Subtask

from .base import BaseAgent

PASS_THRESHOLD = 0.7

_SYSTEM = """You are the Reviewer. Grade the specialist's output against the \
rubric. Be strict but fair. Return ONLY JSON:
{
  "score": 0.0-1.0,
  "passed": true|false,
  "feedback": "what to fix if not passed",
  "rubric_scores": {"<criterion>": true|false}
}
Mark passed=true only if the output genuinely satisfies the subtask."""


class Reviewer(BaseAgent):
    def review(
        self, subtask: Subtask, output: str, rubric: list[str] | None = None
    ) -> ReviewResult:
        rubric = rubric or [
            "addresses the subtask",
            "is accurate and specific",
            "matches the expected output shape",
        ]
        rubric_text = "\n".join(f"- {r}" for r in rubric)
        fallback = ReviewResult(
            score=0.8,
            passed=True,
            feedback="",
            rubric_scores={r: True for r in rubric},
        )
        msgs = self.messages(
            _SYSTEM,
            f"Subtask: {subtask.description}\n"
            f"Expected output: {subtask.expected_output}\n"
            f"Rubric:\n{rubric_text}\n\n"
            f"Specialist output:\n{output}",
        )
        result = structured(
            self.provider, msgs, ReviewResult, model=self.model, fallback=fallback
        )
        # Keep passed consistent with the numeric score / threshold.
        result.passed = result.passed and result.score >= PASS_THRESHOLD
        return result
