"use client";

import { useCallback, useEffect, useState } from "react";
import { TreeStructure, Warning } from "@phosphor-icons/react/dist/ssr";
import {
  getTrace,
  getTraces,
  type SpanNode,
  type TraceFull,
  type TraceSummary,
} from "@/lib/api";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wide text-faint">{label}</span>
      <span className="font-mono text-[13px] tabular-nums text-ink">{value}</span>
    </div>
  );
}

function SpanRow({ span, depth }: { span: SpanNode; depth: number }) {
  const tone =
    span.status === "error" || span.status === "paused"
      ? "text-attention"
      : span.agent === "tool"
        ? "text-faint"
        : "text-ink";
  const tokens = span.tokens_in + span.tokens_out;
  return (
    <>
      <div
        className="flex items-center gap-2 border-b border-hairline-soft py-1.5 pr-3 last:border-0"
        style={{ paddingLeft: 12 + depth * 16 }}
      >
        <span
          className={cn(
            "h-1.5 w-1.5 shrink-0 rounded-full",
            span.status === "error" || span.status === "paused"
              ? "bg-attention"
              : "bg-ink/40",
          )}
        />
        <span className={cn("font-mono text-[12px]", tone)}>{span.name}</span>
        {span.agent && span.agent !== "tool" && (
          <span className="rounded bg-ink/5 px-1.5 py-px text-[10px] text-muted">
            {span.agent}
          </span>
        )}
        <span className="ml-auto flex items-center gap-3 font-mono text-[11px] tabular-nums text-faint">
          {tokens > 0 && <span>{tokens} tok</span>}
          {span.cost_usd > 0 && <span>${span.cost_usd.toFixed(4)}</span>}
          <span className="w-14 text-right">{span.duration_ms.toFixed(0)}ms</span>
        </span>
      </div>
      {span.children.map((c) => (
        <SpanRow key={c.id} span={c} depth={depth + 1} />
      ))}
    </>
  );
}

export function TraceExplorerApp() {
  const [traces, setTraces] = useState<TraceSummary[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [trace, setTrace] = useState<TraceFull | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadList = useCallback((signal?: AbortSignal) => {
    getTraces(signal)
      .then((t) => {
        setTraces(t);
        setSelected((s) => s ?? (t[0]?.task_id ?? null));
      })
      .catch(() => {
        if (!signal?.aborted)
          setError(
            "Couldn't reach the backend. Start it with `uvicorn app.api.main:app --reload` in project15/backend.",
          );
      });
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    loadList(ctrl.signal);
    return () => ctrl.abort();
  }, [loadList]);

  useEffect(() => {
    if (!selected) return;
    const ctrl = new AbortController();
    getTrace(selected, ctrl.signal).then(setTrace).catch(() => {});
    return () => ctrl.abort();
  }, [selected]);

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

  if (traces === null) {
    return (
      <div className="px-5 py-5">
        <Skeleton className="h-40 w-full rounded-card" />
      </div>
    );
  }

  if (traces.length === 0) {
    return (
      <div className="px-5 py-5">
        <EmptyState
          icon={TreeStructure}
          title="No traces yet"
          description="Run a task in New Task. Every run is captured here as a full decision tree with latency, tokens, and cost per node."
        />
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Trace list */}
      <div className="w-52 shrink-0 overflow-y-auto border-r border-hairline p-2">
        {traces.map((t) => (
          <button
            key={t.task_id}
            onClick={() => setSelected(t.task_id)}
            className={cn(
              "mb-0.5 block w-full rounded-md px-2.5 py-2 text-left transition-colors",
              selected === t.task_id ? "bg-ink/[0.06]" : "hover:bg-ink/[0.03]",
            )}
          >
            <p className="truncate text-[12px] text-ink">{t.request || t.task_id}</p>
            <p className="mt-0.5 font-mono text-[10px] text-faint">
              {t.duration_ms.toFixed(0)}ms · ${t.total_cost_usd.toFixed(4)}
              {t.escalations > 0 && " · escalated"}
            </p>
          </button>
        ))}
      </div>

      {/* Tree */}
      <div className="min-w-0 flex-1 overflow-y-auto">
        {trace && (
          <>
            <div className="flex flex-wrap gap-x-8 gap-y-2 border-b border-hairline px-4 py-3">
              <Stat label="Duration" value={`${trace.duration_ms.toFixed(0)}ms`} />
              <Stat label="Tokens" value={String(trace.total_tokens)} />
              <Stat label="Cost" value={`$${trace.total_cost_usd.toFixed(4)}`} />
              <Stat label="Tool calls" value={String(trace.tool_calls)} />
              <Stat label="Escalations" value={String(trace.escalations)} />
            </div>
            <div>
              {trace.spans.map((s) => (
                <SpanRow key={s.id} span={s} depth={0} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
