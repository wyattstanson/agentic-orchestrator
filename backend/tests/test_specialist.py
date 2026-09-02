"""Specialist executes real tool calls and recovers from tool failures."""

from app.agents import Specialist
from app.models import Subtask
from app.models.enums import SpecialistRole
from app.tools import build_default_registry

from .helpers import QueueProvider


def _subtask():
    return Subtask(
        id="s1",
        description="Multiply 6 by 7",
        specialist=SpecialistRole.DATA,
        expected_output="the product",
    )


def test_specialist_calls_a_tool_then_finishes():
    reg = build_default_registry()
    provider = QueueProvider(
        [
            '{"reasoning":"compute it","tool":"calculator","args":{"expression":"6*7"},"final":null}',
            '{"reasoning":"report","tool":null,"args":{},"final":"The result is 42."}',
        ]
    )
    output, _ = Specialist(provider, "m").run(_subtask(), {}, reg)
    assert any(inv.tool == "calculator" and inv.result.ok for inv in reg.log)
    assert "42" in output


def test_specialist_recovers_from_tool_error():
    reg = build_default_registry()
    provider = QueueProvider(
        [
            # `import os` is not a valid arithmetic expression -> tool errors.
            '{"tool":"calculator","args":{"expression":"import os"},"final":null}',
            '{"tool":null,"args":{},"final":"Recovered and produced an answer."}',
        ]
    )
    output, _ = Specialist(provider, "m").run(_subtask(), {}, reg)
    assert reg.log and reg.log[0].result.ok is False
    assert "Recovered" in output  # the run did not crash
