"""Generate the agentic task dataset (master-build-prompt §6).

Approach (b): a template-driven generator. Tasks are original, structurally
inspired by public agentic benchmarks (GAIA / AgentBench / ToolBench-style) but
not copied. Deterministic (seeded), keyless, offline. Some categories emit a
repeated *family* of near-identical requests so the eval harness can show that
memory improves planning on the 2nd/3rd occurrence.

Run:  python -m scripts.generate_dataset
Writes: data/agentic_tasks/tasks.jsonl
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from app.dataset.schema import AgenticTask

OUT = Path(__file__).resolve().parents[1] / "data" / "agentic_tasks" / "tasks.jsonl"

VENDORS = [
    "Datadog", "New Relic", "Grafana", "Splunk", "Honeycomb", "Sentry",
    "Snowflake", "Databricks", "BigQuery", "Redshift", "Fivetran", "Airbyte",
]
COMPANIES = ["Acme", "Globex", "Initech", "Umbrella", "Soylent", "Hooli", "Stark", "Wayne"]
SYSTEMS = ["checkout", "auth", "billing", "search", "recommendations", "notifications", "ingest"]
DATASETS = ["orders", "sessions", "invoices", "events", "shipments", "subscriptions"]
TOPICS = [
    "post-quantum cryptography", "carbon accounting standards", "RAG evaluation",
    "vector database indexing", "GDPR data-retention rules", "WebAuthn adoption",
]

# category -> (id_prefix, specialists, tools, rubric, failure_modes)
SPEC = {
    "research_synthesis": (
        "research",
        ["web_search", "data_extraction", "comparison", "summary"],
        ["web_search", "file_write"],
        ["cites sources", "flags conflicting data", "answer is complete"],
        ["stale pages", "conflicting units"],
    ),
    "competitive_analysis": (
        "compete",
        ["web_search", "feature_matrix", "positioning", "summary"],
        ["web_search", "file_write"],
        ["covers all named competitors", "distinguishes claims from facts", "clear recommendation"],
        ["marketing copy taken as fact", "missing pricing tiers"],
    ),
    "data_pipeline_debug": (
        "pipeline",
        ["reproduce", "inspect_logs", "fix", "verify"],
        ["python_exec", "db_query", "file_read"],
        ["root cause identified", "fix is minimal", "includes a verification step"],
        ["flaky test masks bug", "schema drift"],
    ),
    "support_ticket": (
        "ticket",
        ["lookup_account", "diagnose", "resolve", "reply"],
        ["db_query", "http_get"],
        ["addresses the customer's actual issue", "no unsafe action without approval", "clear reply drafted"],
        ["wrong account matched", "refund without authorisation"],
    ),
    "financial_reconciliation": (
        "recon",
        ["load_ledger", "match_transactions", "flag_discrepancies", "summary"],
        ["db_query", "python_exec", "file_write"],
        ["totals reconcile", "discrepancies itemised", "no adjustment posted without approval"],
        ["currency rounding", "duplicate transactions"],
    ),
    "content_generation": (
        "content",
        ["research", "draft", "fact_check"],
        ["web_search", "file_write"],
        ["every claim is fact-checked", "tone matches the brief", "no fabricated citations"],
        ["hallucinated stats", "outdated figures"],
    ),
    "incident_triage": (
        "incident",
        ["gather_signals", "correlate", "hypothesise", "recommend"],
        ["db_query", "python_exec", "http_get"],
        ["timeline is coherent", "hypothesis is testable", "mitigation proposed"],
        ["alert fatigue noise", "coincident deploys"],
    ),
}

TIERS = ["low", "medium", "high"]


def _pick(rng, seq, k):
    return rng.sample(seq, k)


def build_dataset(seed: int = 7) -> list[AgenticTask]:
    rng = random.Random(seed)
    tasks: list[AgenticTask] = []

    def add(cat, req, tier, *, escalate=False, family=None):
        prefix, subs, tools, rubric, fails = SPEC[cat]
        idx = sum(1 for t in tasks if t.category == cat)
        tasks.append(
            AgenticTask(
                task_id=f"{prefix}-{idx:03d}",
                category=cat,
                request=req,
                expected_subtasks=subs,
                expected_tools=tools,
                complexity_tier=tier,
                should_escalate=escalate,
                reviewer_rubric=rubric,
                known_failure_modes=fails,
                family=family,
            )
        )

    # research_synthesis — includes the repeated "vendor_pricing" family.
    for _ in range(6):
        a, b, c = _pick(rng, VENDORS, 3)
        add(
            "research_synthesis",
            f"Compare {a}, {b}, and {c} pricing models and flag any hidden fees.",
            "medium",
            family="vendor_pricing",
        )
    for _ in range(5):
        t = rng.choice(TOPICS)
        add("research_synthesis", f"Summarise the current state of {t} with sources.", rng.choice(TIERS))

    # competitive_analysis
    for _ in range(10):
        a, b = _pick(rng, VENDORS, 2)
        add("competitive_analysis", f"Build a competitive analysis of {a} vs {b} for a mid-market buyer.", rng.choice(TIERS[1:]))

    # data_pipeline_debug
    for _ in range(11):
        ds = rng.choice(DATASETS)
        add("data_pipeline_debug", f"The nightly {ds} pipeline is dropping rows. Find the root cause and fix it.", rng.choice(TIERS))

    # support_ticket
    for _ in range(10):
        co = rng.choice(COMPANIES)
        sys = rng.choice(SYSTEMS)
        add("support_ticket", f"Customer {co} reports {sys} is failing after login. Diagnose and draft a reply.", rng.choice(TIERS[:2]))

    # financial_reconciliation — sensitive, should escalate on adjustments.
    for _ in range(10):
        co = rng.choice(COMPANIES)
        add(
            "financial_reconciliation",
            f"Reconcile {co}'s Q2 ledger against the payments export and flag discrepancies.",
            "high",
            escalate=True,
            family="ledger_recon",
        )

    # content_generation
    for _ in range(9):
        t = rng.choice(TOPICS)
        add("content_generation", f"Draft a fact-checked explainer on {t} for a technical blog.", rng.choice(TIERS[:2]))

    # incident_triage
    for _ in range(11):
        sys = rng.choice(SYSTEMS)
        add(
            "incident_triage",
            f"Triage the {sys} latency incident from the on-call log and recommend a mitigation.",
            rng.choice(TIERS[1:]),
            escalate=rng.random() < 0.3,
        )

    return tasks


def main() -> None:
    tasks = build_dataset()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "\n".join(t.model_dump_json() for t in tasks) + "\n", encoding="utf-8"
    )
    by_cat: dict[str, int] = {}
    for t in tasks:
        by_cat[t.category] = by_cat.get(t.category, 0) + 1
    print(f"Wrote {len(tasks)} tasks to {OUT}")
    print(json.dumps(by_cat, indent=2))


if __name__ == "__main__":
    main()
