"""Scripted LLM providers for deterministic agent/orchestration tests."""

from __future__ import annotations

from app.llm.base import LLMProvider, LLMResponse, Message


class QueueProvider(LLMProvider):
    """Returns a fixed list of replies in order (for step-by-step loops)."""

    name = "queue"

    def __init__(self, replies: list[str]):
        self._q = list(replies)

    def complete(self, messages, *, model, temperature=0.2, max_tokens=1024, json_mode=False) -> LLMResponse:
        text = self._q.pop(0) if self._q else "{}"
        return LLMResponse(text=text, model=model)


class RoleProvider(LLMProvider):
    """Replies based on which agent is calling (detected from the system prompt),
    so a whole task run is fully deterministic."""

    name = "role"

    def __init__(self, *, plan: str, specialist: str, review: str, synthesis: str = "Final synthesised answer."):
        self.plan = plan
        self.specialist = specialist
        self.review = review
        self.synthesis = synthesis

    def complete(self, messages: list[Message], *, model, temperature=0.2, max_tokens=1024, json_mode=False) -> LLMResponse:
        system = messages[0].content if messages else ""
        if "Supervisor of a multi-agent" in system:
            text = self.plan
        elif "You are the Reviewer" in system:
            text = self.review
        elif "specialist. Complete" in system:
            text = self.specialist
        else:  # synthesis ("You are the Supervisor. Combine ...")
            text = self.synthesis
        return LLMResponse(text=text, model=model)
