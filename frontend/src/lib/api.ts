/** Client for the Orchestrator backend (FastAPI). */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type TaskEvent =
  | { type: "task_started"; task_id: string; request: string }
  | { type: "agent_active"; agent: string }
  | { type: "plan"; plan: PlanPayload }
  | { type: "subtask_started"; id: string; specialist: string; description: string }
  | { type: "tool_call"; id: string; tool: string; ok: boolean; latency_ms: number }
  | { type: "subtask_output"; id: string; output: string }
  | { type: "review"; id: string; passed: boolean; score: number; feedback: string }
  | { type: "subtask_done"; id: string; status: string; attempts: number }
  | { type: "escalation"; id: string; level: string; reason: string }
  | { type: "memory_recall"; hits: { request: string; score: number }[] }
  | { type: "awaiting_approval"; request: ApprovalDto }
  | { type: "approval_resolved"; id: string; decision: string }
  | { type: "aborted"; reason: string }
  | { type: "final"; final: string }
  | {
      type: "done";
      task_id: string;
      subtasks: number;
      tool_calls: number;
      escalations: number;
      cost_usd: number;
      tokens: number;
    }
  | { type: "error"; message: string };

export type SpanNode = {
  id: string;
  name: string;
  agent: string;
  status: "ok" | "error" | "paused";
  duration_ms: number;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  attributes: Record<string, unknown>;
  children: SpanNode[];
};

export type TraceFull = {
  task_id: string;
  request: string;
  created_at: number;
  spans: SpanNode[];
  total_tokens: number;
  total_cost_usd: number;
  duration_ms: number;
  tool_calls: number;
  escalations: number;
  status: string;
};

export type TraceSummary = {
  task_id: string;
  request: string;
  created_at: number;
  duration_ms: number;
  total_tokens: number;
  total_cost_usd: number;
  tool_calls: number;
  escalations: number;
  status: string;
};

export type Analytics = {
  tasks: number;
  total_cost_usd: number;
  avg_cost_usd: number;
  avg_latency_ms: number;
  total_tokens: number;
  escalation_rate: number;
  tool_usage: { tool: string; count: number }[];
  recent: { task_id: string; request: string; cost_usd: number; duration_ms: number; created_at: number }[];
};

export type ApprovalLevel =
  | "notify"
  | "approve_action"
  | "approve_plan"
  | "take_over";

export type ApprovalDto = {
  id: string;
  task_id: string;
  subtask_id: string | null;
  level: ApprovalLevel;
  trigger: string;
  reason: string;
  proposed_action: string;
  agent_reasoning: string;
};

export type ChatTurn = { role: "human" | "agent"; text: string; ts: number };

export type ApprovalFull = ApprovalDto & {
  status: "pending" | "resolved";
  created_at: number;
  chat: ChatTurn[];
};

export type ApprovalDecision = "approve" | "reject" | "modify" | "take_over";

export type MemoryRecordDto = {
  id: string;
  task_id: string;
  request: string;
  summary: string;
  specialists: string[];
  tools: string[];
  facts: string[];
  success: boolean;
  created_at: number;
  last_accessed: number;
  access_count: number;
  importance: number;
};

export type PlanSubtask = {
  id: string;
  description: string;
  specialist: string;
  depends_on: string[];
  expected_output: string;
  complexity: string;
};

export type PlanPayload = {
  task_id: string;
  request: string;
  rationale: string;
  subtasks: PlanSubtask[];
};

export type ToolSpecDto = {
  name: string;
  description: string;
  input_schema: Record<string, string>;
  allowed_specialists: string[];
  rate_limit_per_min: number;
  sensitive: boolean;
};

export type TaskRecordDto = {
  task_id: string;
  request: string;
  status: string;
  cost_usd: number;
  tokens: number;
  tool_calls: number;
  escalations: number;
  subtasks: number;
  duration_ms: number;
  created_at: number;
};

/** Recent task runs, from the database. */
export async function getTasks(signal?: AbortSignal): Promise<TaskRecordDto[]> {
  const res = await fetch(`${API_BASE}/api/tasks`, { signal });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** Fetch the registered tools from the backend. */
export async function getTools(signal?: AbortSignal): Promise<ToolSpecDto[]> {
  const res = await fetch(`${API_BASE}/api/tools`, { signal });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** Fetch what the system remembers across tasks. */
export async function getMemories(signal?: AbortSignal): Promise<MemoryRecordDto[]> {
  const res = await fetch(`${API_BASE}/api/memory`, { signal });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** Delete one memory (data-removal). */
export async function deleteMemory(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/memory/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
}

/** Consolidate near-duplicates and prune stale memories. */
export async function maintainMemory(): Promise<{ consolidated: number; pruned: number }> {
  const res = await fetch(`${API_BASE}/api/memory/maintain`, { method: "POST" });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** List past execution traces (summaries). */
export async function getTraces(signal?: AbortSignal): Promise<TraceSummary[]> {
  const res = await fetch(`${API_BASE}/api/traces`, { signal });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** Fetch one full trace tree. */
export async function getTrace(taskId: string, signal?: AbortSignal): Promise<TraceFull> {
  const res = await fetch(`${API_BASE}/api/traces/${taskId}`, { signal });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** Aggregate cost & performance analytics. */
export async function getAnalytics(signal?: AbortSignal): Promise<Analytics> {
  const res = await fetch(`${API_BASE}/api/analytics`, { signal });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

export type EvalReport = {
  tasks?: number;
  overall?: { success_rate: number; escalation_rate: number; avg_cost_usd: number; avg_latency_ms: number };
  memory?: {
    family_tasks: number;
    first_occurrence_recall_rate: number;
    repeat_occurrence_recall_rate: number;
    avg_recall_score_on_repeats: number;
  };
};

/** The offline eval-harness report (from eval/run_harness.py), if present. */
export async function getEvalReport(signal?: AbortSignal): Promise<EvalReport> {
  const res = await fetch(`${API_BASE}/api/eval/report`, { signal });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** Pending human-approval requests (paused runs). */
export async function getApprovals(signal?: AbortSignal): Promise<ApprovalFull[]> {
  const res = await fetch(`${API_BASE}/api/approvals`, { signal });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** Resolve an approval — unblocks the paused run. */
export async function resolveApproval(
  id: string,
  decision: ApprovalDecision,
  modifiedOutput?: string,
  note?: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/approvals/${id}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, modified_output: modifiedOutput, note }),
  });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
}

/** Ask the agent a clarifying question about a pending approval. */
export async function chatApproval(
  id: string,
  question: string,
): Promise<{ answer: string; chat: ChatTurn[] }> {
  const res = await fetch(`${API_BASE}/api/approvals/${id}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  return res.json();
}

/** POST a request and invoke `onEvent` for each streamed SSE event. */
export async function streamTask(
  request: string,
  onEvent: (event: TaskEvent) => void,
  approvePlan = false,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/tasks/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ request, approve_plan: approvePlan }),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`Backend responded ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) >= 0) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const line = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      try {
        onEvent(JSON.parse(line.slice(5).trim()) as TaskEvent);
      } catch {
        /* ignore malformed frame */
      }
    }
  }
}
