"""Provider-agnostic LLM interface.

Every provider (Groq today; Anthropic/OpenAI/Ollama later) implements the same
small surface, so the agent layer never imports a vendor SDK directly.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Iterator, Literal, TypeVar

from pydantic import BaseModel, ValidationError

Role = Literal["system", "user", "assistant"]


class Message(BaseModel):
    role: Role
    content: str


class LLMResponse(BaseModel):
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMProvider(ABC):
    """The one interface the agents depend on."""

    name: str = "base"

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse: ...

    def stream(
        self,
        messages: list[Message],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Iterator[str]:
        """Default: yield the whole completion once. Real providers override."""
        yield self.complete(
            messages, model=model, temperature=temperature, max_tokens=max_tokens
        ).text


T = TypeVar("T", bound=BaseModel)


def _extract_json(text: str) -> str:
    """Pull the first balanced JSON object out of a completion."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]


def structured(
    provider: LLMProvider,
    messages: list[Message],
    schema: type[T],
    *,
    model: str,
    temperature: float = 0.0,
    max_tokens: int = 1500,
    max_retries: int = 1,
    fallback: T | None = None,
) -> T:
    """Request JSON, parse and validate it against `schema`.

    Retries once with a corrective nudge. If the provider is the offline echo
    stub (or all retries fail) and a `fallback` is supplied, returns it so the
    graph still runs without a live key.
    """
    convo = list(messages)
    last_err: str = ""
    for attempt in range(max_retries + 1):
        resp = provider.complete(
            convo,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        try:
            return schema.model_validate_json(_extract_json(resp.text))
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            last_err = str(exc)
            if attempt < max_retries:
                convo.append(Message(role="assistant", content=resp.text))
                convo.append(
                    Message(
                        role="user",
                        content=(
                            "That was not valid JSON for the required schema. "
                            f"Fix these errors and reply with ONLY the JSON:\n{last_err}"
                        ),
                    )
                )
    if fallback is not None:
        return fallback
    raise ValueError(f"structured() failed to parse {schema.__name__}: {last_err}")
