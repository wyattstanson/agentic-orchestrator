"""The task-decomposition schema — the supervisor's structured output."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .enums import ComplexityTier, SpecialistRole


class Subtask(BaseModel):
    """One unit of work in a plan, assigned to a single specialist."""

    id: str = Field(description="Stable id, e.g. 's1'. Referenced by depends_on.")
    description: str = Field(description="What this subtask must accomplish.")
    specialist: SpecialistRole
    inputs: list[str] = Field(
        default_factory=list,
        description="Inputs required — literals or 'output of <id>'.",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Ids of subtasks whose output this one needs first.",
    )
    expected_output: str = Field(description="Shape of the expected result.")
    complexity: ComplexityTier = ComplexityTier.MEDIUM


class Plan(BaseModel):
    """A dependency-aware decomposition of a request."""

    task_id: str
    request: str
    subtasks: list[Subtask] = Field(default_factory=list)
    rationale: str = Field(
        default="", description="Short note on the planning approach."
    )

    def dependency_ok(self) -> bool:
        """Every depends_on id must reference a real subtask (no cycles allowed)."""
        ids = {s.id for s in self.subtasks}
        for s in self.subtasks:
            for dep in s.depends_on:
                if dep not in ids or dep == s.id:
                    return False
        return not self._has_cycle()

    def _has_cycle(self) -> bool:
        graph = {s.id: set(s.depends_on) for s in self.subtasks}
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {sid: WHITE for sid in graph}

        def visit(node: str) -> bool:
            color[node] = GRAY
            for nxt in graph.get(node, ()):  # dep edges
                if color.get(nxt) == GRAY:
                    return True
                if color.get(nxt) == WHITE and visit(nxt):
                    return True
            color[node] = BLACK
            return False

        return any(color[sid] == WHITE and visit(sid) for sid in graph)

    def execution_order(self) -> list[list[str]]:
        """Topological layers — ids in the same layer can run in parallel."""
        remaining = {s.id: set(s.depends_on) for s in self.subtasks}
        layers: list[list[str]] = []
        while remaining:
            ready = sorted(sid for sid, deps in remaining.items() if not deps)
            if not ready:
                break  # cycle / unresolved dependency; caller should validate first
            layers.append(ready)
            for sid in ready:
                remaining.pop(sid)
            for deps in remaining.values():
                deps.difference_update(ready)
        return layers
