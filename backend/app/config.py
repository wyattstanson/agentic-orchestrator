"""Application configuration, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM provider
    llm_provider: str = Field(default="echo")
    groq_api_key: str = Field(default="")
    llm_model_planner: str = Field(default="llama-3.3-70b-versatile")
    llm_model_specialist: str = Field(default="llama-3.1-8b-instant")
    llm_model_reviewer: str = Field(default="llama-3.3-70b-versatile")

    # Tool sandbox
    tool_workspace: str = Field(default="./_workspace")
    code_exec_timeout: int = Field(default=10)

    # Memory
    working_memory: str = Field(default="memory")  # memory | redis
    redis_url: str = Field(default="")
    memory_backend: str = Field(default="local")  # local | chroma
    memory_dir: str = Field(default="./_memory")

    # Persistence (tasks, traces, approvals)
    # Empty -> local SQLite under data_dir. For Supabase, set the Postgres URI:
    #   postgresql+psycopg://postgres:<pwd>@db.<ref>.supabase.co:5432/postgres
    database_url: str = Field(default="")
    data_dir: str = Field(default="./_data")
    store_backend: str = Field(default="sql")  # sql | file

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        p = Path(self.data_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(p / 'orchestrator.db').as_posix()}"

    @property
    def workspace_path(self) -> Path:
        p = Path(self.tool_workspace).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
