"use client";

import { useMemo, useRef, useState } from "react";
import { PaperPlaneTilt, Warning } from "@phosphor-icons/react/dist/ssr";
import { streamTask, type PlanSubtask, type TaskEvent } from "@/lib/api";
import { AgentConstellation } from "@/components/constellation/agent-constellation";
import {
  DEFAULT_EDGES,
  DEFAULT_NODES,
  type AgentStatus,
  type ConstellationState,
} from "@/components/constellation/types";
import { Button } from "@/components/ui/button";
import { ListSection, ListGroup, ListRow } from "@/components/ui/list";
import { StatusDot } from "@/components/ui/status-dot";

type StepStatus = "pending" | "running" | "done" | "failed";
type StepState = { status: StepStatus; score?: number; tools: number; output?: string };

const DOT: Record<StepStatus, "idle" | "running" | "done" | "failed"> = {
  pending: "idle",
  running: "running",
  done: "done",
  failed: "failed",
};

export function NewTaskApp() {
  const [request, setRequest] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subtasks, setSubtasks] = useState<PlanSubtask[]>([]);
  const [steps, setSteps] = useState<Record<string, StepState>>({});
  const [nodeStatus, setNodeStatus] = useState<Record<string, AgentStatus>>({});
  const [finalText, setFinalText] = useState("");
  const [recalled, setRecalled] = useState<{ request: string; score: number }[]>([]);
  const [paused, setPaused] = useState<{ reason: string } | null>(null);
  const [aborted, setAborted] = useState<string | null>(null);
  const [approvePlan, setApprovePlan] = useState(false);
  const subtasksRef = useRef<PlanSubtask[]>([]);

  const constellation: ConstellationState = useMemo(() => {
    const nodes = DEFAULT_NODES.map((n) => ({
      ...n,
      status: nodeStatus[n.id] ?? ("idle" as AgentStatus),
    }));
    const active = nodes.find((n) => n.status === "active")?.id ?? null;
    const edges = DEFAULT_EDGES.map((e) => ({
      ...e,
      active: !!active && (e.to === active || e.from === active),
    }));
    return { nodes, edges };
  }, [nodeStatus]);

  function activate(agent: string) {
    setNodeStatus((prev) => {
      const next = { ...prev };
      for (const k of Object.keys(next)) if (next[k] === "active") next[k] = "done";
      next[agent] = "active";
      return next;
    });
  }

  function onEvent(ev: TaskEvent) {
    switch (ev.type) {
      case "memory_recall":
        setRecalled(ev.hits);
        break;
      case "awaiting_approval":
        setPaused({ reason: ev.request.reason });
        break;
      case "approval_resolved":
        setPaused(null);
        break;
      case "aborted":
        setAborted(ev.reason);
        setRunning(false);
        break;
      case "agent_active":
        activate(ev.agent);
        break;
      case "plan":
        subtasksRef.current = ev.plan.subtasks;
        setSubtasks(ev.plan.subtasks);
        setSteps(
          Object.fromEntries(
            ev.plan.subtasks.map((s) => [s.id, { status: "pending", tools: 0 }]),
          ),
        );
        break;
      case "subtask_started":
        setSteps((p) => ({ ...p, [ev.id]: { ...p[ev.id], status: "running" } }));
        break;
      case "tool_call":
        setSteps((p) => ({
          ...p,
          [ev.id]: { ...p[ev.id], tools: (p[ev.id]?.tools ?? 0) + 1 },
        }));
        break;
      case "subtask_output":
        setSteps((p) => ({ ...p, [ev.id]: { ...p[ev.id], output: ev.output } }));
        break;
      case "review":
        setSteps((p) => ({ ...p, [ev.id]: { ...p[ev.id], score: ev.score } }));
        break;
      case "subtask_done": {
        const st = ev.status === "done" ? "done" : "failed";
        setSteps((p) => ({ ...p, [ev.id]: { ...p[ev.id], status: st } }));
        if (st === "failed") {
          const sub = subtasksRef.current.find((s) => s.id === ev.id);
          if (sub) setNodeStatus((prev) => ({ ...prev, [sub.specialist]: "failed" }));
        }
        break;
      }
      case "final":
        setFinalText(ev.final);
        break;
      case "done":
        setNodeStatus((prev) => {
          const next = { ...prev };
          for (const k of Object.keys(next)) if (next[k] === "active") next[k] = "done";
          return next;
        });
        setRunning(false);
        break;
      case "error":
        setError(ev.message);
        setRunning(false);
        break;
    }
  }

  async function run() {
    if (!request.trim() || running) return;
    setError(null);
    setSubtasks([]);
    setSteps({});
    setFinalText("");
    setNodeStatus({});
    setRecalled([]);
    setPaused(null);
    setAborted(null);
    setRunning(true);
    try {
      await streamTask(request.trim(), onEvent, approvePlan);
    } catch {
      setError(
        "Couldn't reach the backend. Start it with `uvicorn app.api.main:app --reload` in project15/backend, then try again.",
      );
      setRunning(false);
    }
  }

  return (
    <div className="px-5 py-5">
      <div className="rounded-card bg-surface p-3">
        <textarea
          value={request}
          onChange={(e) => setRequest(e.target.value)}
          placeholder="Describe a task — e.g. Compare three vendors' pricing and flag hidden fees."
          rows={3}
          className="w-full resize-none bg-transparent text-[14px] text-ink outline-none placeholder:text-faint"
        />
        <div className="mt-2 flex items-center justify-between">
          <label className="flex items-center gap-1.5 text-[11px] text-faint">
            <input
              type="checkbox"
              checked={approvePlan}
              onChange={(e) => setApprovePlan(e.target.checked)}
              className="accent-accent"
            />
            Require my approval of the plan first
          </label>
          <Button variant="primary" size="sm" onClick={run} disabled={running || !request.trim()}>
            <PaperPlaneTilt size={14} weight="bold" />
            {running ? "Running…" : "Run task"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="mt-4 flex items-start gap-2 rounded-card bg-attention/10 p-3 text-[12px] text-attention">
          <Warning size={15} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {paused && (
        <div className="mt-4 flex items-start gap-2 rounded-card bg-attention/10 p-3 text-[12px] text-attention">
          <Warning size={15} className="mt-0.5 shrink-0" />
          <span>
            Paused — {paused.reason} Open{" "}
            <span className="font-medium">Review Queue</span> to approve, modify,
            reject, or take over.
          </span>
        </div>
      )}

      {aborted && (
        <div className="mt-4 flex items-start gap-2 rounded-card bg-attention/10 p-3 text-[12px] text-attention">
          <Warning size={15} className="mt-0.5 shrink-0" />
          <span>Run aborted — {aborted}</span>
        </div>
      )}

      {recalled.length > 0 && (
        <div className="mt-4 rounded-card bg-surface p-3">
          <p className="text-[12px] font-medium text-ink">
            Recalled {recalled.length} similar past task
            {recalled.length > 1 ? "s" : ""} to plan faster
          </p>
          <ul className="mt-1.5 space-y-1">
            {recalled.map((h, i) => (
              <li key={i} className="flex items-center justify-between gap-2 text-[12px] text-muted">
                <span className="truncate">{h.request}</span>
                <span className="font-mono text-[11px] tabular-nums text-faint">
                  {(h.score * 100).toFixed(0)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {subtasks.length > 0 && (
        <>
          <div className="mt-4 overflow-hidden rounded-card bg-surface">
            <AgentConstellation state={constellation} className="mx-auto max-w-lg" />
          </div>

          <ListSection title="Plan" className="mt-6">
            <ListGroup>
              {subtasks.map((s) => {
                const st = steps[s.id];
                return (
                  <ListRow
                    key={s.id}
                    leading={<StatusDot status={DOT[st?.status ?? "pending"]} />}
                    title={s.description}
                    subtitle={`${s.specialist}${st?.tools ? ` · ${st.tools} tool call${st.tools > 1 ? "s" : ""}` : ""}`}
                    trailing={
                      st?.score != null ? (
                        <span className="text-[12px] tabular-nums text-faint">
                          {st.score.toFixed(2)}
                        </span>
                      ) : undefined
                    }
                  />
                );
              })}
            </ListGroup>
          </ListSection>
        </>
      )}

      {finalText && (
        <ListSection title="Final Answer" className="mt-6 mb-0">
          <div className="rounded-card bg-surface p-4 text-[13px] leading-relaxed whitespace-pre-wrap text-ink">
            {finalText}
          </div>
        </ListSection>
      )}
    </div>
  );
}
