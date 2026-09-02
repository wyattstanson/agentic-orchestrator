"use client";

import { useEffect, useState } from "react";
import { ChartBar, Warning } from "@phosphor-icons/react/dist/ssr";
import { getAnalytics, getEvalReport, type Analytics, type EvalReport } from "@/lib/api";
import { StatTile } from "@/components/ui/stat-tile";
import { ListSection } from "@/components/ui/list";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";

function ToolUsage({ data }: { data: { tool: string; count: number }[] }) {
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="space-y-2 rounded-card bg-surface p-4">
      {data.map((d) => (
        <div key={d.tool} className="flex items-center gap-3">
          <span className="w-24 shrink-0 truncate font-mono text-[12px] text-muted">
            {d.tool}
          </span>
          <div className="h-4 flex-1 overflow-hidden rounded-sm bg-ink/[0.05]">
            <div
              className="h-full rounded-sm bg-ink/70"
              style={{ width: `${(d.count / max) * 100}%` }}
            />
          </div>
          <span className="w-8 text-right font-mono text-[12px] tabular-nums text-faint">
            {d.count}
          </span>
        </div>
      ))}
    </div>
  );
}

function CostBars({ data }: { data: Analytics["recent"] }) {
  const max = Math.max(...data.map((d) => d.cost_usd), 0.0001);
  return (
    <div className="rounded-card bg-surface p-4">
      <div className="flex h-32 items-end gap-1.5">
        {data
          .slice()
          .reverse()
          .map((d) => (
            <div
              key={d.task_id}
              className="group relative flex-1 rounded-t-sm bg-ink/60 transition-colors hover:bg-accent"
              style={{ height: `${Math.max((d.cost_usd / max) * 100, 3)}%` }}
              title={`${d.request.slice(0, 40)} — $${d.cost_usd.toFixed(4)}`}
            />
          ))}
      </div>
      <p className="mt-2 text-[11px] text-faint">Cost per recent run (hover for detail)</p>
    </div>
  );
}

export function AnalyticsApp() {
  const [data, setData] = useState<Analytics | null>(null);
  const [evalReport, setEvalReport] = useState<EvalReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    getAnalytics(ctrl.signal)
      .then(setData)
      .catch(() => {
        if (!ctrl.signal.aborted)
          setError(
            "Couldn't reach the backend. Start it with `uvicorn app.api.main:app --reload` in project15/backend.",
          );
      });
    getEvalReport(ctrl.signal)
      .then(setEvalReport)
      .catch(() => {});
    return () => ctrl.abort();
  }, []);

  if (error) {
    return (
      <div className="px-5 py-5">
        <div className="flex items-start gap-2 rounded-card bg-attention/10 p-3 text-[12px] text-attention">
          <Warning size={15} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="px-5 py-5">
        <Skeleton className="h-40 w-full rounded-card" />
      </div>
    );
  }

  if (data.tasks === 0) {
    return (
      <div className="px-5 py-5">
        <EmptyState
          icon={ChartBar}
          title="Not enough runs to chart"
          description="Run a few tasks in New Task. Cost, latency, tool-usage, and escalation trends aggregate here."
        />
      </div>
    );
  }

  return (
    <div className="px-5 py-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Tasks run" value={String(data.tasks)} />
        <StatTile label="Avg cost / task" value={`$${data.avg_cost_usd.toFixed(4)}`} />
        <StatTile
          label="Avg latency"
          value={(data.avg_latency_ms / 1000).toFixed(1)}
          unit="s"
        />
        <StatTile
          label="Escalation rate"
          value={`${Math.round(data.escalation_rate * 100)}`}
          unit="%"
        />
      </div>

      {evalReport?.memory && evalReport.overall && (
        <ListSection title={`Dataset eval · ${evalReport.tasks} tasks`} className="mt-6">
          <div className="rounded-card bg-surface p-4">
            <p className="text-[13px] text-ink">
              Memory recalled a relevant prior run on{" "}
              <span className="font-semibold">
                {Math.round(evalReport.memory.repeat_occurrence_recall_rate * 100)}%
              </span>{" "}
              of repeated tasks (0% on first occurrence) — similarity{" "}
              {evalReport.memory.avg_recall_score_on_repeats.toFixed(2)}. That's the
              memory-improves-planning result, measured over the full dataset.
            </p>
            <div className="mt-3 flex flex-wrap gap-x-8 gap-y-2 font-mono text-[12px] text-muted">
              <span>success {Math.round(evalReport.overall.success_rate * 100)}%</span>
              <span>avg ${evalReport.overall.avg_cost_usd.toFixed(5)}/task</span>
              <span>avg {(evalReport.overall.avg_latency_ms / 1000).toFixed(2)}s</span>
            </div>
          </div>
        </ListSection>
      )}

      <ListSection title="Cost per recent run" className="mt-6">
        <CostBars data={data.recent} />
      </ListSection>

      <ListSection title="Tool usage" className="mt-6 mb-0">
        {data.tool_usage.length > 0 ? (
          <ToolUsage data={data.tool_usage} />
        ) : (
          <p className="rounded-card bg-surface p-4 text-[13px] text-faint">
            No tool calls recorded yet.
          </p>
        )}
      </ListSection>
    </div>
  );
}
