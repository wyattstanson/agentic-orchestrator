"""Human-in-the-loop approval queue.

When a run escalates, it calls `ApprovalQueue.submit(request)` which **blocks**
the run's thread until a human resolves it via `resolve(...)`. Execution stays
paused in between — this is what makes the human a real gate, not a log line.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import EscalationLevel, EscalationTrigger

Decision = Literal["approve", "reject", "modify", "take_over"]


class Resolution(BaseModel):
    decision: Decision
    modified_output: str | None = None
    note: str | None = None
    resolved_at: float = Field(default_factory=time.time)


class ChatTurn(BaseModel):
    role: Literal["human", "agent"]
    text: str
    ts: float = Field(default_factory=time.time)


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    task_id: str
    subtask_id: str | None = None
    level: EscalationLevel
    trigger: EscalationTrigger
    reason: str
    proposed_action: str = ""
    agent_reasoning: str = ""
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    status: Literal["pending", "resolved"] = "pending"
    resolution: Resolution | None = None
    chat: list[ChatTurn] = Field(default_factory=list)


class ApprovalQueue:
    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}
        self._events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    # -- called from the run thread -----------------------------------------
    def submit(self, request: ApprovalRequest, *, timeout: float | None = None) -> Resolution:
        """Register a pending approval and block until it's resolved."""
        with self._lock:
            self._requests[request.id] = request
            self._events[request.id] = threading.Event()
        event = self._events[request.id]
        if not event.wait(timeout=timeout):
            # Timed out waiting for a human — fail safe by rejecting.
            return Resolution(decision="reject", note="timed out")
        return request.resolution or Resolution(decision="reject", note="no resolution")

    # -- called from the API thread -----------------------------------------
    def resolve(self, request_id: str, resolution: Resolution) -> bool:
        with self._lock:
            req = self._requests.get(request_id)
            event = self._events.get(request_id)
            if req is None or event is None or req.status == "resolved":
                return False
            req.resolution = resolution
            req.status = "resolved"
        event.set()
        return True

    def pending(self) -> list[ApprovalRequest]:
        with self._lock:
            return [r for r in self._requests.values() if r.status == "pending"]

    def get(self, request_id: str) -> ApprovalRequest | None:
        with self._lock:
            return self._requests.get(request_id)

    def add_chat(self, request_id: str, turn: ChatTurn) -> bool:
        with self._lock:
            req = self._requests.get(request_id)
            if req is None:
                return False
            req.chat.append(turn)
            return True


_queue: ApprovalQueue | None = None


def get_queue() -> ApprovalQueue:
    global _queue
    if _queue is None:
        _queue = ApprovalQueue()
    return _queue
