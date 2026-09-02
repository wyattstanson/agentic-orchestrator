"""Tool schemas and the first-class invocation log entry."""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from .enums import SpecialistRole


class ToolSpec(BaseModel):
    """Metadata describing a registered tool (master-build-prompt §2.3)."""

    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    allowed_specialists: list[SpecialistRole] = Field(default_factory=list)
    rate_limit_per_min: int = 60
    sensitive: bool = Field(
        default=False,
        description="If true, use is a candidate for human escalation.",
    )


class ToolResult(BaseModel):
    ok: bool
    output: Any = None
    error: str | None = None
    latency_ms: float = 0.0


class ToolInvocation(BaseModel):
    """A logged tool call — a first-class object, not a debug print."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    tool: str
    specialist: SpecialistRole | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    result: ToolResult
    ts: float = Field(default_factory=time.time)
