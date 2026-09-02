/*
  Phase-0 sample data. This exists only so the shell renders with realistic
  content before the backend streams live runs (master-build-prompt §6 wants
  seeded demo content, not empty screens). Every surface that uses it shows a
  "sample" marker so nothing is passed off as a real run. Replace in Phase 1+.
*/

export type TaskRow = {
  id: string;
  request: string;
  category: string;
  status: "running" | "escalated" | "done" | "failed";
  costUsd: number;
  latencyMs: number;
  agent: string;
};

export type Escalation = {
  id: string;
  taskId: string;
  reason: string;
  level: "Notify" | "Approve action" | "Approve plan" | "Take over";
  waitingMs: number;
};

export const SAMPLE_KPIS = {
  activeTasks: 3,
  escalations: 2,
  avgCostUsd: 0.42,
  avgLatencyS: 18.6,
  successRate: 0.91,
} as const;

export const SAMPLE_TASKS: TaskRow[] = [
  {
    id: "research-014",
    request: "Compare three vendors' pricing models and flag hidden fees",
    category: "research_synthesis",
    status: "running",
    costUsd: 0.38,
    latencyMs: 14200,
    agent: "Research",
  },
  {
    id: "recon-006",
    request: "Reconcile Q2 ledger against the payments export",
    category: "financial_reconciliation",
    status: "escalated",
    costUsd: 0.71,
    latencyMs: 26800,
    agent: "Data / Analysis",
  },
  {
    id: "triage-021",
    request: "Triage the checkout latency incident from the on-call log",
    category: "incident_triage",
    status: "running",
    costUsd: 0.29,
    latencyMs: 9100,
    agent: "Code Exec",
  },
  {
    id: "content-033",
    request: "Draft a fact-checked changelog from the merged PRs",
    category: "content_generation",
    status: "done",
    costUsd: 0.18,
    latencyMs: 7400,
    agent: "Writing",
  },
];

export const SAMPLE_ESCALATIONS: Escalation[] = [
  {
    id: "esc-004",
    taskId: "recon-006",
    reason: "Sensitive action: proposes a $1,240 balancing adjustment",
    level: "Approve action",
    waitingMs: 42000,
  },
  {
    id: "esc-005",
    taskId: "research-014",
    reason: "Reviewer rejected the pricing table twice (conflicting currency units)",
    level: "Approve plan",
    waitingMs: 15000,
  },
];

export function formatUsd(n: number): string {
  return `$${n.toFixed(2)}`;
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = Math.floor(s / 60);
  return `${m}m ${Math.round(s % 60)}s`;
}
