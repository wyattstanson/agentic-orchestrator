"""Human-in-the-loop: the queue blocks a run until a human decides."""

import threading
import time

from app.hitl import ApprovalQueue, ApprovalRequest, Resolution
from app.models.enums import EscalationLevel, EscalationTrigger
from app.orchestration import Orchestrator

from .helpers import RoleProvider

PLAN = (
    '{"task_id":"t1","request":"do X","rationale":"r",'
    '"subtasks":[{"id":"s1","description":"gather","specialist":"research",'
    '"inputs":[],"depends_on":[],"expected_output":"notes","complexity":"low"}]}'
)


def test_queue_blocks_until_resolved():
    q = ApprovalQueue()
    req = ApprovalRequest(
        task_id="t",
        level=EscalationLevel.APPROVE_ACTION,
        trigger=EscalationTrigger.REVIEW_REJECTED,
        reason="rejected twice",
    )
    result: dict = {}

    def worker():
        result["res"] = q.submit(req)

    th = threading.Thread(target=worker)
    th.start()
    for _ in range(200):  # wait for it to register as pending
        if q.pending():
            break
        time.sleep(0.01)

    assert q.pending() and q.pending()[0].id == req.id
    assert q.resolve(req.id, Resolution(decision="approve")) is True
    th.join(timeout=2)
    assert result["res"].decision == "approve"
    assert not q.pending()  # moved to resolved


def _run_until_resolved(decision: str, modified: str | None = None) -> list[dict]:
    q = ApprovalQueue()
    provider = RoleProvider(
        plan=PLAN,
        specialist='{"final":"weak answer","tool":null,"args":{}}',
        review='{"score":0.2,"passed":false,"feedback":"insufficient","rubric_scores":{}}',
    )
    orch = Orchestrator(provider=provider, resolver=q.submit)
    events: list[dict] = []

    def run():
        for e in orch.stream_run("do X"):
            events.append(e)

    th = threading.Thread(target=run)
    th.start()
    for _ in range(300):
        if q.pending():
            break
        time.sleep(0.01)
    pending = q.pending()[0]
    q.resolve(pending.id, Resolution(decision=decision, modified_output=modified))  # type: ignore[arg-type]
    th.join(timeout=5)
    return events


def test_run_pauses_then_resumes_on_approve():
    events = _run_until_resolved("approve")
    types = [e["type"] for e in events]
    assert "awaiting_approval" in types
    assert "approval_resolved" in types
    done = next(e for e in events if e["type"] == "subtask_done")
    assert done["status"] == "done"  # approved despite failing review


def test_run_reject_keeps_subtask_failed():
    events = _run_until_resolved("reject")
    done = next(e for e in events if e["type"] == "subtask_done")
    assert done["status"] == "failed"


def test_run_modify_completes_with_override():
    events = _run_until_resolved("modify", modified="a corrected answer")
    types = [e["type"] for e in events]
    done = next(e for e in events if e["type"] == "subtask_done")
    assert done["status"] == "done"
    assert "escalation" not in types  # human handled it, not an unhandled escalation
