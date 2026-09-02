"""Shared agent base."""

from __future__ import annotations

from app.llm import LLMProvider, Message


class BaseAgent:
    def __init__(self, provider: LLMProvider, model: str):
        self.provider = provider
        self.model = model

    @staticmethod
    def messages(system: str, user: str) -> list[Message]:
        return [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]
