"""Specialist — executes one subtask with real tool access (a bounded ReAct loop)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.llm import Message, structured
from app.models import Subtask
from app.tools import ToolRegistry

from .base import BaseAgent

MAX_STEPS = 4


class ToolAction(BaseModel):
    reasoning: str = ""
    tool: str | None = Field(default=None, description="Tool to call, or null.")
    args: dict[str, Any] = Field(default_factory=dict)
    final: str | None = Field(default=None, description="Final answer, or null.")


class Specialist(BaseAgent):
    def _system(self, subtask: Subtask, registry: ToolRegistry) -> str:
        tools = registry.specs_for(subtask.specialist)
        tool_lines = "\n".join(
            f"- {t.name}({', '.join(t.input_schema)}): {t.description}" for t in tools
        ) or "- (no tools available)"
        return (
            f"You are the {subtask.specialist.value} specialist. Complete the "
            "subtask. You may use tools, one at a time.\n\n"
            f"Tools:\n{tool_lines}\n\n"
            "At each step reply with ONLY a JSON object:\n"
            '{"reasoning": "...", "tool": "<name|null>", "args": {...}, '
            '"final": "<answer|null>"}\n'
            "Set `tool` to call a tool; set `final` (and tool=null) when done."
        )

    def run(
        self, subtask: Subtask, context: dict[str, str], registry: ToolRegistry
    ) -> tuple[str, str]:
        ctx = "\n".join(f"[{k}] {v}" for k, v in context.items()) or "(none)"
        msgs = self.messages(
            self._system(subtask, registry),
            f"Subtask: {subtask.description}\n"
            f"Expected output: {subtask.expected_output}\n"
            f"Upstream results:\n{ctx}",
        )
        reasoning: list[str] = []
        for _ in range(MAX_STEPS):
            action = structured(
                self.provider,
                msgs,
                ToolAction,
                model=self.model,
                fallback=ToolAction(final=f"(offline) {subtask.expected_output}"),
            )
            if action.reasoning:
                reasoning.append(action.reasoning)
            if action.final:
                return action.final, "\n".join(reasoning)
            if action.tool:
                result = registry.invoke(
                    action.tool, action.args, specialist=subtask.specialist
                )
                obs = (
                    str(result.output)[:1500]
                    if result.ok
                    else f"ERROR: {result.error}"
                )
                msgs.append(Message(role="assistant", content=action.model_dump_json()))
                msgs.append(Message(role="user", content=f"Observation: {obs}"))
            else:
                break

        # Loop exhausted — ask for a direct answer.
        msgs.append(
            Message(role="user", content="Now give the final answer as plain text.")
        )
        text = self.provider.complete(
            msgs, model=self.model, temperature=0.3, max_tokens=900
        ).text
        return text, "\n".join(reasoning)
