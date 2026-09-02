"""The tool registry — registration, permissioning, rate limits, and a
first-class invocation log."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any, Callable

from app.models.enums import SpecialistRole
from app.models.tools import ToolInvocation, ToolResult, ToolSpec

ToolFn = Callable[[dict[str, Any]], Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}
        self._fns: dict[str, ToolFn] = {}
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self.log: list[ToolInvocation] = []

    # -- registration -------------------------------------------------------
    def register(self, spec: ToolSpec, fn: ToolFn) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._specs[spec.name] = spec
        self._fns[spec.name] = fn

    def get(self, name: str) -> ToolSpec | None:
        return self._specs.get(name)

    def specs(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def specs_for(self, role: SpecialistRole) -> list[ToolSpec]:
        return [
            s
            for s in self._specs.values()
            if not s.allowed_specialists or role in s.allowed_specialists
        ]

    # -- invocation ---------------------------------------------------------
    def _rate_ok(self, name: str, limit: int) -> bool:
        now = time.time()
        window = self._calls[name]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= limit:
            return False
        window.append(now)
        return True

    def invoke(
        self,
        name: str,
        args: dict[str, Any],
        *,
        specialist: SpecialistRole | None = None,
    ) -> ToolResult:
        spec = self._specs.get(name)
        if spec is None:
            return self._logged(name, specialist, args, ToolResult(ok=False, error=f"No such tool: {name}"))

        if specialist and spec.allowed_specialists and specialist not in spec.allowed_specialists:
            return self._logged(
                name, specialist, args,
                ToolResult(ok=False, error=f"{specialist.value} may not call {name}"),
            )

        if not self._rate_ok(name, spec.rate_limit_per_min):
            return self._logged(
                name, specialist, args,
                ToolResult(ok=False, error=f"Rate limit exceeded for {name}"),
            )

        start = time.perf_counter()
        try:
            output = self._fns[name](args)
            result = ToolResult(ok=True, output=output)
        except Exception as exc:  # tools must never crash the graph
            result = ToolResult(ok=False, error=f"{type(exc).__name__}: {exc}")
        result.latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return self._logged(name, specialist, args, result)

    def _logged(
        self, name: str, specialist: SpecialistRole | None,
        args: dict[str, Any], result: ToolResult,
    ) -> ToolResult:
        self.log.append(
            ToolInvocation(tool=name, specialist=specialist, args=args, result=result)
        )
        return result
