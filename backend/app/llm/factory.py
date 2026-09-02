"""Select the LLM provider from configuration."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings

from .base import LLMProvider
from .echo_provider import EchoProvider
from .groq_provider import GroqProvider


@lru_cache
def get_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "groq":
        return GroqProvider(api_key=settings.groq_api_key)
    if provider == "echo":
        return EchoProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
