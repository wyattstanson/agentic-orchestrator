"""Deterministic, no-network provider for tests and offline development.

It never pretends to be a real model: it echoes structured, predictable text so
the orchestration graph can run end-to-end without a key. Callers that need real
JSON pass a `fallback` to `structured()`.
"""

from __future__ import annotations

from .base import LLMProvider, LLMResponse, Message


class EchoProvider(LLMProvider):
    name = "echo"

    def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        if json_mode:
            # Deliberately empty — structured() will use the caller's fallback.
            text = "{}"
        else:
            text = f"[echo:{model}] {last_user[:400]}"
        return LLMResponse(
            text=text,
            model=model,
            prompt_tokens=sum(len(m.content) // 4 for m in messages),
            completion_tokens=len(text) // 4,
        )
