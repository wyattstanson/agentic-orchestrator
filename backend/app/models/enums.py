"""Shared enums for the agent domain."""

from __future__ import annotations

from enum import Enum


class SpecialistRole(str, Enum):
    RESEARCH = "research"
    DATA = "data"
    WRITING = "writing"
    CODE = "code"


class ComplexityTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EscalationLevel(str, Enum):
    """Graded human intervention (master-build-prompt §4)."""

    NOTIFY = "notify"
    APPROVE_ACTION = "approve_action"
    APPROVE_PLAN = "approve_plan"
    TAKE_OVER = "take_over"


class EscalationTrigger(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    REPEATED_FAILURE = "repeated_failure"
    SENSITIVE_ACTION = "sensitive_action"
    REVIEW_REJECTED = "review_rejected"
    USER_REQUESTED = "user_requested"
