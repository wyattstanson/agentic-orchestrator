"""Wraps any LLMProvider to attribute tokens and cost to the open trace span."""

from __future__ import annotations

from typing import Iterator

from app.llm.base import LLMProvider, LLMResponse, Message

from .trace import Tracer


class TracingProvider(LLMProvider):
    name = "tracing"

    def __init__(self, inner: LLMProvider, tracer: Tracer):
        self._inner = inner
        self._tracer = tracer

    def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        resp = self._inner.complete(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        self._tracer.record_usage(model, resp.prompt_tokens, resp.completion_tokens)
        return resp

    def stream(
        self, messages: list[Message], *, model: str, temperature: float = 0.2, max_tokens: int = 1024
    ) -> Iterator[str]:
        yield from self._inner.stream(
            messages, model=model, temperature=temperature, max_tokens=max_tokens
        )
