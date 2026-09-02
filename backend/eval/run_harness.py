"""Run the eval harness against the dataset and write a report.

Usage:
    python -m eval.run_harness            # full dataset, active LLM provider
    python -m eval.run_harness --limit 20 # a quick subset

Writes eval/report.json and prints a summary table. Runs offline on the `echo`
provider by default (set LLM_PROVIDER=groq in .env for real-model numbers).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.dataset import load_tasks
from app.dataset.harness import run_harness

REPORT = Path(__file__).resolve().parent / "report.json"


def _print_table(title: str, groups: dict) -> None:
    print(f"\n{title}")
    print(f"  {'group':<24}{'n':>4}{'success':>9}{'escal':>7}{'$avg':>10}{'ms avg':>9}")
    for name, s in groups.items():
        print(
            f"  {name:<24}{s['n']:>4}{s['success_rate']:>9.2f}"
            f"{s['escalation_rate']:>7.2f}{s['avg_cost_usd']:>10.5f}{s['avg_latency_ms']:>9.0f}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks. Running{' ' + str(args.limit) if args.limit else ''}…")
    report = run_harness(tasks, limit=args.limit)

    o = report["overall"]
    print("\n=== OVERALL ===")
    print(f"  tasks           {report['tasks']}")
    print(f"  success rate    {o['success_rate']:.2%}")
    print(f"  escalation rate {o['escalation_rate']:.2%}")
    print(f"  avg cost        ${o['avg_cost_usd']:.5f}")
    print(f"  avg latency     {o['avg_latency_ms']:.0f} ms")
    print(f"  total cost      ${o['total_cost_usd']:.4f}")

    _print_table("=== BY CATEGORY ===", report["by_category"])
    _print_table("=== BY TIER ===", report["by_tier"])

    m = report["memory"]
    print("\n=== MEMORY IMPROVES PLANNING ===")
    print(f"  family tasks                 {m['family_tasks']}")
    print(f"  recall on 1st occurrence     {m['first_occurrence_recall_rate']:.0%}")
    print(f"  recall on repeat occurrences {m['repeat_occurrence_recall_rate']:.0%}")
    print(f"  avg recall score (repeats)   {m['avg_recall_score_on_repeats']:.2f}")

    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {REPORT}")


if __name__ == "__main__":
    main()
