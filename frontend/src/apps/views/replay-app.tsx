"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowsClockwise,
  CaretLeft,
  CaretRight,
  Warning,
} from "@phosphor-icons/react/dist/ssr";
import {
  getTrace,
  getTraces,
  streamTask,
  type SpanNode,
  type TraceFull,
  type TraceSummary,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";

type FlatSpan = { span: SpanNode; depth: number };

function flatten(spans: SpanNode[], depth = 0, out: FlatSpan[] = []): FlatSpan[] {
  for (const s of spans) {
    out.push({ span: s, depth });
    flatten(s.children, depth + 1, out);
  }
  return out;
}

type Rerun = { cost: number; tokens: number; escalations: number } | null;

export function ReplayApp() {
  const [traces, setTraces] = useState<TraceSummary[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [trace, setTrace] = useState<TraceFull | null>(null);
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [rerun, setRerun] = useState<Rerun>(null);
  const [rerunning, setRerunning] = useState(false);

  const load = useCallback((signal?: AbortSignal) => {
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
    load(ctrl.signal);
    return () => ctrl.abort();
  }, [load]);

  useEffect(() => {
    if (!selected) return;
    const ctrl = new AbortController();
    getTrace(selected, ctrl.signal)
      .then((t) => {
        setTrace(t);
        setStep(0);
        setRerun(null);
      })
      .catch(() => {});
    return () => ctrl.abort();
  }, [selected]);

  const flat = useMemo(() => (trace ? flatten(trace.spans) : []), [trace]);
  const current = flat[step]?.span;

  async function doRerun() {
    if (!trace) return;
    setRerunning(true);
    setRerun(null);
    try {
      await streamTask(trace.request, (ev) => {
        if (ev.type === "done")
          setRerun({
            cost: ev.cost_usd,
            tokens: ev.tokens,
            escalations: ev.escalations,
          });
      });
    } finally {
      setRerunning(false);
      load();
    }
  }

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

  if (!traces || traces.length === 0 || !trace) {
    return (
      <div className="px-5 py-5">
        <EmptyState
          icon={ArrowsClockwise}
          title="Nothing to replay yet"
          description="Run a task in New Task, then step through its decisions here and re-run it to see how the outcome diverges."
        />
      </div>
    );
  }

  const diff = (a: number, b: number) => {
    const d = b - a;
    const sign = d > 0 ? "+" : "";
    return `${sign}${d.toFixed(d < 0.01 && d > -0.01 ? 4 : 2)}`;
  };

  return (
    <div className="px-5 py-5">
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={selected ?? ""}
          onChange={(e) => setSelected(e.target.value)}
          className="h-8 rounded-md border border-hairline bg-surface px-2 text-[13px] text-ink outline-none"
        >
          {traces.map((t) => (
            <option key={t.task_id} value={t.task_id}>
              {(t.request || t.task_id).slice(0, 40)}
            </option>
          ))}
        </select>
        <Button variant="secondary" size="sm" onClick={doRerun} disabled={rerunning}>
          <ArrowsClockwise size={14} />
          {rerunning ? "Re-running…" : "Re-run & diff"}
        </Button>
      </div>

      {/* Step-through */}
      <div className="mt-4 rounded-card bg-surface p-4">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-faint">
            Step {step + 1} of {flat.length}
          </span>
          <div className="flex gap-1.5">
            <Button variant="secondary" size="icon" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
              <CaretLeft size={14} />
            </Button>
            <Button variant="secondary" size="icon" disabled={step >= flat.length - 1} onClick={() => setStep((s) => s + 1)}>
              <CaretRight size={14} />
            </Button>
          </div>
        </div>
        {current && (
          <div className="mt-3">
            <p className="font-mono text-[14px] text-ink">{current.name}</p>
            <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 font-mono text-[12px] text-muted">
              {current.agent && <span>agent: {current.agent}</span>}
              <span>status: {current.status}</span>
              <span>{current.duration_ms.toFixed(0)}ms</span>
              <span>{current.tokens_in + current.tokens_out} tok</span>
              <span>${current.cost_usd.toFixed(4)}</span>
            </div>
            {Object.keys(current.attributes).length > 0 && (
              <pre className="mt-2 overflow-auto rounded-md bg-canvas/60 p-2 font-mono text-[11px] text-faint">
                {JSON.stringify(current.attributes, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>

      {/* Diff after re-run */}
      {rerun && (
        <div className="mt-4 rounded-card bg-surface p-4">
          <p className="mb-2 text-[13px] font-medium text-ink">Re-run vs original</p>
          <div className="grid grid-cols-3 gap-3 font-mono text-[12px]">
            <div>
              <p className="text-faint">Cost</p>
              <p className="text-ink">
                ${trace.total_cost_usd.toFixed(4)} → ${rerun.cost.toFixed(4)}{" "}
                <span className="text-muted">({diff(trace.total_cost_usd, rerun.cost)})</span>
              </p>
            </div>
            <div>
              <p className="text-faint">Tokens</p>
              <p className="text-ink">
                {trace.total_tokens} → {rerun.tokens}
              </p>
            </div>
            <div>
              <p className="text-faint">Escalations</p>
              <p className="text-ink">
                {trace.escalations} → {rerun.escalations}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Flattened span list */}
      <div className="mt-4 overflow-hidden rounded-card bg-surface">
        {flat.map((f, i) => (
          <button
            key={f.span.id}
            onClick={() => setStep(i)}
            className={cn(
              "flex w-full items-center gap-2 border-b border-hairline-soft py-1.5 pr-3 text-left transition-colors last:border-0",
              i === step ? "bg-ink/[0.06]" : "hover:bg-ink/[0.02]",
            )}
            style={{ paddingLeft: 12 + f.depth * 16 }}
          >
            <span
              className={cn(
                "h-1.5 w-1.5 shrink-0 rounded-full",
                f.span.status === "ok" ? "bg-ink/40" : "bg-attention",
              )}
            />
            <span className="font-mono text-[12px] text-muted">{f.span.name}</span>
            <span className="ml-auto font-mono text-[11px] tabular-nums text-faint">
              {f.span.duration_ms.toFixed(0)}ms
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
