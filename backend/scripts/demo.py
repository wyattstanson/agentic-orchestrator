"""Run one task through the orchestrator and print the trace.

    python -m scripts.demo "Compare three vendors' pricing and flag hidden fees"

Uses whatever LLM_PROVIDER is set in .env (echo works offline).
"""

from __future__ import annotations

import sys

from app.orchestration import Orchestrator


def main() -> None:
    request = " ".join(sys.argv[1:]) or "Summarise the key risks in a vendor contract."
    orch = Orchestrator()
    state = orch.run(request)

    plan = state["plan"]
    print(f"\n=== PLAN ({plan.task_id}) ===")
    for s in plan.subtasks:
        dep = f" <- {', '.join(s.depends_on)}" if s.depends_on else ""
        print(f"  {s.id} [{s.specialist.value}] {s.description}{dep}")

    print("\n=== EXECUTION ===")
    for sid, run in state["runs"].items():
        score = f"{run.review.score:.2f}" if run.review else "n/a"
        print(f"  {sid}: {run.status} (attempts={run.attempts}, score={score})")

    if state["escalations"]:
        print("\n=== ESCALATIONS ===")
        for e in state["escalations"]:
            print(f"  [{e.level.value}] {e.reason}")

    print("\n=== TOOL CALLS ===")
    for inv in orch.registry.log:
        print(f"  {inv.tool} ok={inv.result.ok} ({inv.result.latency_ms}ms)")

    print("\n=== FINAL ===")
    print(state["final"])


if __name__ == "__main__":
    main()
