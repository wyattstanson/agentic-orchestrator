"""Groq provider — OpenAI-compatible, free tier, fast inference."""

from __future__ import annotations

import time
from typing import Iterator

from .base import LLMProvider, LLMResponse, Message


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is empty. Get a free key at "
                "https://console.groq.com/keys or set LLM_PROVIDER=echo."
            )
        # Imported lazily so the package installs/imports without the SDK
        # present when running in echo mode.
        from groq import Groq

        self._client = Groq(api_key=api_key)

    def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        kwargs = {
            "model": model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(3):  # simple backoff on transient errors
            try:
                resp = self._client.chat.completions.create(**kwargs)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(0.6 * (attempt + 1))

        usage = resp.usage
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            model=model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )

    def stream(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            model=model,
            messages=[m.model_dump() for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
