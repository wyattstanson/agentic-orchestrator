"""Supervisor — decomposition, delegation planning, and final synthesis."""

from __future__ import annotations

import uuid

from app.llm import Message, structured
from app.models import Plan, Subtask
from app.models.enums import ComplexityTier, SpecialistRole

from .base import BaseAgent

_PLANNER_SYSTEM = """You are the Supervisor of a multi-agent system. Break the \
user's request into an ordered, dependency-aware plan.

Available specialists:
- research: gathers and synthesises information (web/http, reading).
- data: analysis, calculation, code-driven data work.
- writing: drafting, summarising, structured prose.
- code: writing and running code, debugging.

Return ONLY a JSON object matching this schema:
{
  "task_id": string,
  "request": string,
  "rationale": string,
  "subtasks": [
    {
      "id": "s1",
      "description": string,
      "specialist": "research|data|writing|code",
      "inputs": [string],
      "depends_on": ["s0"],
      "expected_output": string,
      "complexity": "low|medium|high"
    }
  ]
}

Rules: ids are unique and stable; depends_on references only earlier ids; keep \
plans minimal (2-5 subtasks) but complete; put a subtask that needs another's \
result in depends_on."""


class Supervisor(BaseAgent):
    def decompose(
        self,
        request: str,
        *,
        task_id: str | None = None,
        memory_hints: list[str] | None = None,
    ) -> Plan:
        task_id = task_id or f"task-{uuid.uuid4().hex[:8]}"
        fallback = Plan(
            task_id=task_id,
            request=request,
            rationale="Fallback plan (offline / unparseable model output).",
            subtasks=[
                Subtask(
                    id="s1",
                    description=f"Research and gather what is needed for: {request}",
                    specialist=SpecialistRole.RESEARCH,
                    expected_output="Key findings and sources.",
                    complexity=ComplexityTier.MEDIUM,
                ),
                Subtask(
                    id="s2",
                    description="Synthesise the findings into a clear answer.",
                    specialist=SpecialistRole.WRITING,
                    depends_on=["s1"],
                    inputs=["output of s1"],
                    expected_output="A concise written answer.",
                    complexity=ComplexityTier.LOW,
                ),
            ],
        )
        recall = ""
        if memory_hints:
            joined = "\n".join(f"- {h}" for h in memory_hints)
            recall = (
                "\n\nSimilar past tasks the system has handled well (reuse what "
                f"applies to plan faster):\n{joined}"
            )
        msgs = self.messages(
            _PLANNER_SYSTEM, f"Request:\n{request}{recall}\n\ntask_id: {task_id}"
        )
        plan = structured(
            self.provider, msgs, Plan, model=self.model, fallback=fallback
        )
        # Guard against a model that returned an invalid dependency graph.
        if not plan.subtasks or not plan.dependency_ok():
            return fallback
        plan.task_id = task_id
        plan.request = request
        return plan

    def synthesize(self, request: str, completed: dict[str, str]) -> str:
        joined = "\n\n".join(f"[{sid}]\n{out}" for sid, out in completed.items())
        msgs = self.messages(
            "You are the Supervisor. Combine the specialists' outputs into one "
            "clear, well-structured final answer to the user's request. Do not "
            "mention the internal subtask ids.",
            f"Request:\n{request}\n\nSpecialist outputs:\n{joined}",
        )
        return self.provider.complete(
            msgs, model=self.model, temperature=0.3, max_tokens=1200
        ).text
