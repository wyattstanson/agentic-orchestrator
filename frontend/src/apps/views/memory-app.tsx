"use client";

import { useCallback, useEffect, useState } from "react";
import { Brain, Trash, Warning, Broom } from "@phosphor-icons/react/dist/ssr";
import {
  deleteMemory,
  getMemories,
  maintainMemory,
  type MemoryRecordDto,
} from "@/lib/api";
import { ListSection, ListGroup, ListRow } from "@/components/ui/list";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";

export function MemoryApp() {
  const [records, setRecords] = useState<MemoryRecordDto[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback((signal?: AbortSignal) => {
    getMemories(signal)
      .then(setRecords)
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

  async function remove(id: string) {
    await deleteMemory(id);
    setRecords((prev) => prev?.filter((r) => r.id !== id) ?? null);
  }

  async function maintain() {
    setBusy(true);
    try {
      await maintainMemory();
      load();
    } finally {
      setBusy(false);
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

  if (records === null) {
    return (
      <div className="px-5 py-5">
        <div className="overflow-hidden rounded-card bg-surface">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="border-b border-hairline-soft px-4 py-3 last:border-0">
              <Skeleton className="h-3 w-64" />
              <Skeleton className="mt-2 h-2.5 w-40" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (records.length === 0) {
    return (
      <div className="px-5 py-5">
        <EmptyState
          icon={Brain}
          title="Nothing remembered yet"
          description="Run a few tasks in New Task. After each one, the system distils what it learned into long-term memory — and recalls it on similar future tasks."
        />
      </div>
    );
  }

  return (
    <div className="px-5 py-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-[13px] text-muted">
          {records.length} memories, ranked by importance (frequency × recency).
        </p>
        <Button variant="secondary" size="sm" onClick={maintain} disabled={busy}>
          <Broom size={14} />
          {busy ? "Working…" : "Consolidate & prune"}
        </Button>
      </div>

      <ListSection title="Long-term Memory" className="mb-0">
        <ListGroup>
          {records.map((r) => (
            <ListRow
              key={r.id}
              title={r.request}
              subtitle={
                <span>
                  {r.summary}
                  <span className="mt-0.5 block font-mono text-[11px] text-faint">
                    {r.specialists.join(", ") || "—"}
                    {r.tools.length > 0 && ` · tools: ${r.tools.join(", ")}`}
                    {` · used ${r.access_count}×`}
                  </span>
                </span>
              }
              trailing={
                <>
                  <span
                    className="font-mono text-[11px] tabular-nums text-faint"
                    title="importance (frequency × recency)"
                  >
                    {r.importance.toFixed(2)}
                  </span>
                  <button
                    aria-label="Delete memory"
                    onClick={() => remove(r.id)}
                    className="grid h-6 w-6 place-items-center rounded-md text-faint transition-colors hover:bg-attention/10 hover:text-attention"
                  >
                    <Trash size={14} />
                  </button>
                </>
              }
            />
          ))}
        </ListGroup>
      </ListSection>
    </div>
  );
}
