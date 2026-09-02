"""Tool registry: invocation, permissioning, rate limits, logging, builtins."""

from app.models.enums import SpecialistRole
from app.models.tools import ToolSpec
from app.tools import ToolRegistry, build_default_registry


def test_builtins_registered():
    reg = build_default_registry()
    names = {s.name for s in reg.specs()}
    assert {
        "file_write",
        "file_read",
        "calculator",
        "python_exec",
        "http_get",
        "web_search",
        "db_query",
    } <= names


def test_calculator_runs():
    reg = build_default_registry()
    res = reg.invoke("calculator", {"expression": "2 + 3 * 4"})
    assert res.ok and res.output == 14


def test_permission_enforced():
    reg = build_default_registry()
    # python_exec is not allowed for the research specialist.
    res = reg.invoke("python_exec", {"code": "print(1)"}, specialist=SpecialistRole.RESEARCH)
    assert not res.ok and "may not" in (res.error or "")


def test_unknown_tool():
    reg = build_default_registry()
    res = reg.invoke("nope", {})
    assert not res.ok and "No such tool" in (res.error or "")


def test_rate_limit():
    reg = ToolRegistry()
    reg.register(ToolSpec(name="ping", description="", rate_limit_per_min=2), lambda a: "pong")
    assert reg.invoke("ping", {}).ok
    assert reg.invoke("ping", {}).ok
    third = reg.invoke("ping", {})
    assert not third.ok and "Rate limit" in (third.error or "")


def test_invocation_logged():
    reg = build_default_registry()
    reg.invoke("calculator", {"expression": "1+1"})
    assert reg.log and reg.log[-1].tool == "calculator"
    assert reg.log[-1].result.latency_ms >= 0
