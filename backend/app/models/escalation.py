"""Human-in-the-loop escalation payload (master-build-prompt §4)."""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from .enums import EscalationLevel, EscalationTrigger


class Escalation(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    task_id: str
    subtask_id: str | None = None
    trigger: EscalationTrigger
    level: EscalationLevel
    reason: str
    # The full context handed to the reviewer to decide on.
    proposed_action: str = ""
    agent_reasoning: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    resolved: bool = False
    resolution: str | None = None


# Which level each trigger maps to by default (don't route everything to the
# heaviest level).
DEFAULT_LEVEL: dict[EscalationTrigger, EscalationLevel] = {
    EscalationTrigger.LOW_CONFIDENCE: EscalationLevel.APPROVE_PLAN,
    EscalationTrigger.REPEATED_FAILURE: EscalationLevel.TAKE_OVER,
    EscalationTrigger.SENSITIVE_ACTION: EscalationLevel.APPROVE_ACTION,
    EscalationTrigger.REVIEW_REJECTED: EscalationLevel.APPROVE_ACTION,
    EscalationTrigger.USER_REQUESTED: EscalationLevel.NOTIFY,
}
