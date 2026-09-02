"use client";

import { useEffect, useState } from "react";
import { Warning, Wrench } from "@phosphor-icons/react/dist/ssr";
import { getTools, type ToolSpecDto } from "@/lib/api";
import { ListSection, ListGroup, ListRow } from "@/components/ui/list";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";

export function ToolRegistryApp() {
  const [tools, setTools] = useState<ToolSpecDto[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    getTools(ctrl.signal)
      .then(setTools)
      .catch(() => {
        if (!ctrl.signal.aborted)
          setError(
            "Couldn't reach the backend. Start it with `uvicorn app.api.main:app --reload` in project15/backend.",
          );
      });
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

  if (tools === null) {
    return (
      <div className="px-5 py-5">
        <div className="overflow-hidden rounded-card bg-surface">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 border-b border-hairline-soft px-4 py-3 last:border-0">
              <div className="flex-1">
                <Skeleton className="h-3 w-28" />
                <Skeleton className="mt-2 h-2.5 w-56" />
              </div>
              <Skeleton className="h-3 w-12" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (tools.length === 0) {
    return (
      <div className="px-5 py-5">
        <EmptyState icon={Wrench} title="No tools registered" description="The registry is empty." />
      </div>
    );
  }

  return (
    <div className="px-5 py-5">
      <p className="mb-4 text-[13px] text-muted">
        {tools.length} tools available to the specialists. Each call is logged
        with inputs, latency, and success.
      </p>
      <ListSection title="Registered Tools" className="mb-0">
        <ListGroup>
          {tools.map((tool) => (
            <ListRow
              key={tool.name}
              title={
                <span className="flex items-center gap-2">
                  <span className="font-mono text-[13px] text-ink">{tool.name}</span>
                  {tool.sensitive && (
                    <span className="rounded-full bg-attention/12 px-1.5 py-px text-[10px] text-attention">
                      sensitive
                    </span>
                  )}
                </span>
              }
              subtitle={
                <span>
                  {tool.description}
                  <span className="mt-0.5 block font-mono text-[11px] text-faint">
                    ({Object.keys(tool.input_schema).join(", ") || "no args"})
                    {tool.allowed_specialists.length > 0 &&
                      ` · ${tool.allowed_specialists.join(", ")}`}
                  </span>
                </span>
              }
              trailing={
                <span className="font-mono text-[11px] tabular-nums text-faint">
                  {tool.rate_limit_per_min}/min
                </span>
              }
            />
          ))}
        </ListGroup>
      </ListSection>
    </div>
  );
}
