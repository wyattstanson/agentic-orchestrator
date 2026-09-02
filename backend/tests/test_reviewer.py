"""Reviewer scoring — a scripted provider drives a deterministic verdict."""

from app.agents import Reviewer
from app.llm.base import LLMProvider, LLMResponse, Message
from app.models import Subtask
from app.models.enums import SpecialistRole


class ScriptedProvider(LLMProvider):
    name = "scripted"

    def __init__(self, reply: str):
        self._reply = reply

    def complete(self, messages: list[Message], *, model, temperature=0.2, max_tokens=1024, json_mode=False) -> LLMResponse:
        return LLMResponse(text=self._reply, model=model)


def _subtask():
    return Subtask(
        id="s1", description="Build a pricing table",
        specialist=SpecialistRole.DATA, expected_output="a complete table",
    )


def test_reviewer_rejects_low_score():
    provider = ScriptedProvider(
        '{"score": 0.4, "passed": true, "feedback": "missing sources", "rubric_scores": {}}'
    )
    review = Reviewer(provider, "m").review(_subtask(), "half a table")
    # Even though the model said passed=true, the threshold forces a rejection.
    assert review.passed is False
    assert review.feedback


def test_reviewer_accepts_high_score():
    provider = ScriptedProvider(
        '{"score": 0.92, "passed": true, "feedback": "", "rubric_scores": {}}'
    )
    review = Reviewer(provider, "m").review(_subtask(), "a full, sourced table")
    assert review.passed is True
