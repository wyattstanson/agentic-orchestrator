"use client";

import { useEffect, useState } from "react";
import { PlusCircle } from "@phosphor-icons/react/dist/ssr";
import { AgentConstellation } from "@/components/constellation/agent-constellation";
import { Button } from "@/components/ui/button";
import { ListSection, ListGroup, ListRow } from "@/components/ui/list";
import { StatusDot } from "@/components/ui/status-dot";
import { getTasks, type TaskRecordDto } from "@/lib/api";
import {
  SAMPLE_ESCALATIONS,
  SAMPLE_KPIS,
  SAMPLE_TASKS,
  formatDuration,
  formatUsd,
} from "@/lib/mock";

function dbStatus(s: string): "done" | "escalated" | "failed" | "running" {
  if (s === "done" || s === "escalated" || s === "failed") return s;
  return "running";
}

function Readout({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[11px] text-faint">{label}</span>
      <span className="text-[13px] tabular-nums text-ink">{value}</span>
    </div>
  );
}

export function CommandCenterApp() {
  const [tasks, setTasks] = useState<TaskRecordDto[] | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    getTasks(ctrl.signal)
      .then(setTasks)
      .catch(() => {}); // backend down → fall back to sample data
    return () => ctrl.abort();
  }, []);

  const real = tasks && tasks.length > 0;
  const totalCost = real ? tasks!.reduce((a, t) => a + t.cost_usd, 0) : 0;

  return (
    <div className="px-5 py-5">
      <div className="mb-5 flex items-center justify-between gap-3">
        <p className="text-[12px] text-muted">
          {real ? (
            <>
              {tasks!.length} runs ·{" "}
              {tasks!.filter((t) => t.escalations > 0).length} escalated ·{" "}
              {formatUsd(totalCost / tasks!.length)} avg · $
              {totalCost.toFixed(4)} total
            </>
          ) : (
            <>
              {SAMPLE_TASKS.filter((t) => t.status === "running").length} running ·{" "}
              {SAMPLE_ESCALATIONS.length} need review ·{" "}
              {formatUsd(SAMPLE_KPIS.avgCostUsd)} avg ·{" "}
              {Math.round(SAMPLE_KPIS.successRate * 100)}% success
              <span className="ml-2 text-faint">· sample data</span>
            </>
          )}
        </p>
        <Button variant="primary" size="sm">
          <PlusCircle size={15} weight="bold" />
          New Task
        </Button>
      </div>

      <ListSection title="Current Run">
        <div className="overflow-hidden rounded-card bg-surface">
          <div className="flex items-center gap-3 border-b border-hairline-soft px-4 py-3">
            <StatusDot status="running" />
            <div className="min-w-0 flex-1">
              <div className="truncate text-[13px] text-ink">
                Compare three vendors&apos; pricing models and flag hidden fees
              </div>
              <div className="mt-0.5 text-[12px] text-faint">
                research-014 · research synthesis
              </div>
            </div>
          </div>
          <div className="px-2 pb-1 pt-3">
            <AgentConstellation className="mx-auto max-w-xl" />
          </div>
          <div className="flex flex-wrap gap-x-8 gap-y-3 border-t border-hairline-soft px-4 py-3">
            <Readout label="Step" value="Reviewer grading" />
            <Readout label="Cost so far" value="$0.38" />
            <Readout label="Elapsed" value="14.2s" />
            <Readout label="Tokens" value="41.6k" />
          </div>
        </div>
      </ListSection>

      <ListSection title="Needs Review">
        <ListGroup>
          {SAMPLE_ESCALATIONS.map((esc) => (
            <ListRow
              key={esc.id}
              leading={<StatusDot status="escalated" />}
              title={esc.reason}
              subtitle={`${esc.taskId} · ${esc.level.toLowerCase()} · waiting ${formatDuration(esc.waitingMs)}`}
              trailing={
                <Button variant="secondary" size="sm">
                  Review
                </Button>
              }
            />
          ))}
        </ListGroup>
      </ListSection>

      <ListSection title="Recent Tasks" className="mb-0">
        <ListGroup>
          {real
            ? tasks!.map((task) => (
                <ListRow
                  key={task.task_id}
                  leading={<StatusDot status={dbStatus(task.status)} />}
                  title={task.request}
                  subtitle={`${task.status} · ${task.subtasks} subtasks · ${task.tokens} tok`}
                  trailing={
                    <span className="flex items-center gap-3">
                      <span className="text-[12px] tabular-nums text-faint">
                        {formatUsd(task.cost_usd)}
                      </span>
                      <span className="w-14 text-right text-[12px] tabular-nums text-faint">
                        {formatDuration(task.duration_ms)}
                      </span>
                    </span>
                  }
                />
              ))
            : SAMPLE_TASKS.map((task) => (
                <ListRow
                  key={task.id}
                  leading={<StatusDot status={task.status} />}
                  title={task.request}
                  subtitle={`${task.agent} · ${task.category.replace(/_/g, " ")}`}
                  trailing={
                    <span className="w-14 text-right text-[12px] tabular-nums text-faint">
                      {formatDuration(task.latencyMs)}
                    </span>
                  }
                />
              ))}
        </ListGroup>
      </ListSection>
    </div>
  );
}
