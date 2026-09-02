"""End-to-end graph smoke test (offline, echo provider).

Skips if langgraph isn't installed yet so the rest of the suite still runs.
"""

import pytest

pytest.importorskip("langgraph")

from app.orchestration import Orchestrator  # noqa: E402


def test_graph_runs_end_to_end_offline():
    orch = Orchestrator()
    result = orch.run("Summarise the key risks in a vendor contract")

    assert result["plan"] is not None
    assert result["plan"].subtasks
    # Every subtask produced a run and an output.
    assert result["runs"]
    assert result["completed"]
    # Offline reviewer fallback passes, so nothing should have failed/escalated.
    assert result["final"]
    assert result["errors"] == []
