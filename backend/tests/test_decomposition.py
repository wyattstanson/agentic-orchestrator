"""Decomposition engine: plan validity, dependency graph, execution order."""

from app.agents import Supervisor
from app.llm.echo_provider import EchoProvider
from app.models import Plan, Subtask
from app.models.enums import SpecialistRole


def _plan(subtasks):
    return Plan(task_id="t1", request="r", subtasks=subtasks)


def test_dependency_ok_accepts_valid_dag():
    plan = _plan(
        [
            Subtask(id="s1", description="a", specialist=SpecialistRole.RESEARCH, expected_output="x"),
            Subtask(id="s2", description="b", specialist=SpecialistRole.WRITING, depends_on=["s1"], expected_output="y"),
        ]
    )
    assert plan.dependency_ok()


def test_dependency_ok_rejects_missing_dep():
    plan = _plan(
        [Subtask(id="s1", description="a", specialist=SpecialistRole.RESEARCH, depends_on=["s9"], expected_output="x")]
    )
    assert not plan.dependency_ok()


def test_dependency_ok_rejects_cycle():
    plan = _plan(
        [
            Subtask(id="s1", description="a", specialist=SpecialistRole.DATA, depends_on=["s2"], expected_output="x"),
            Subtask(id="s2", description="b", specialist=SpecialistRole.DATA, depends_on=["s1"], expected_output="y"),
        ]
    )
    assert not plan.dependency_ok()


def test_execution_order_layers_a_diamond():
    plan = _plan(
        [
            Subtask(id="s1", description="root", specialist=SpecialistRole.RESEARCH, expected_output="x"),
            Subtask(id="s2", description="l", specialist=SpecialistRole.DATA, depends_on=["s1"], expected_output="x"),
            Subtask(id="s3", description="r", specialist=SpecialistRole.DATA, depends_on=["s1"], expected_output="x"),
            Subtask(id="s4", description="join", specialist=SpecialistRole.WRITING, depends_on=["s2", "s3"], expected_output="x"),
        ]
    )
    layers = plan.execution_order()
    assert layers == [["s1"], ["s2", "s3"], ["s4"]]


def test_supervisor_offline_returns_valid_fallback_plan():
    sup = Supervisor(EchoProvider(), "m")
    plan = sup.decompose("Compare three vendors' pricing and flag hidden fees")
    assert plan.subtasks
    assert plan.dependency_ok()
    assert plan.execution_order()  # non-empty, resolvable
