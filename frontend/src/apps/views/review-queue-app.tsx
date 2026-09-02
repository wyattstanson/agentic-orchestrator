"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Warning,
  ShieldCheck,
  Check,
  X,
  PencilSimple,
  HandPalm,
  PaperPlaneRight,
} from "@phosphor-icons/react/dist/ssr";
import {
  chatApproval,
  getApprovals,
  resolveApproval,
  type ApprovalDecision,
  type ApprovalFull,
  type ChatTurn,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

const LEVEL_LABEL: Record<string, string> = {
  notify: "Notify",
  approve_action: "Approve action",
  approve_plan: "Approve plan",
  take_over: "Take over",
};

function ApprovalCard({
  approval,
  onResolved,
}: {
  approval: ApprovalFull;
  onResolved: () => void;
}) {
  const [mode, setMode] = useState<"modify" | "take_over" | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<ChatTurn[]>(approval.chat ?? []);
  const [asking, setAsking] = useState(false);

  async function resolve(decision: ApprovalDecision, output?: string) {
    setBusy(true);
    try {
      await resolveApproval(approval.id, decision, output);
      onResolved();
    } finally {
      setBusy(false);
    }
  }

  async function ask() {
    if (!question.trim()) return;
    setAsking(true);
    try {
      const res = await chatApproval(approval.id, question.trim());
      setChat(res.chat);
      setQuestion("");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="rounded-card bg-surface p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="rounded-full bg-attention/12 px-2 py-0.5 text-[11px] font-medium text-attention">
          {LEVEL_LABEL[approval.level] ?? approval.level}
        </span>
        <span className="font-mono text-[11px] text-faint">
          {approval.task_id}
          {approval.subtask_id ? ` · ${approval.subtask_id}` : ""}
        </span>
      </div>

      <p className="mt-2 text-[14px] text-ink">{approval.reason}</p>

      {approval.proposed_action && (
        <div className="mt-3">
          <p className="mb-1 text-[11px] font-medium text-faint">Proposed</p>
          <pre className="max-h-32 overflow-auto rounded-md bg-canvas/60 p-2.5 font-mono text-[12px] whitespace-pre-wrap text-muted">
            {approval.proposed_action}
          </pre>
        </div>
      )}
      {approval.agent_reasoning && (
        <p className="mt-2 text-[12px] italic text-muted">
          Agent: {approval.agent_reasoning}
        </p>
      )}

      {/* Differentiated actions */}
      {mode === null ? (
        <div className="mt-4 flex flex-wrap gap-2">
          <Button variant="primary" size="sm" disabled={busy} onClick={() => resolve("approve")}>
            <Check size={14} weight="bold" /> Approve
          </Button>
          <Button variant="danger" size="sm" disabled={busy} onClick={() => resolve("reject")}>
            <X size={14} weight="bold" /> Reject
          </Button>
          <Button variant="secondary" size="sm" disabled={busy} onClick={() => setMode("modify")}>
            <PencilSimple size={14} /> Modify
          </Button>
          <Button variant="secondary" size="sm" disabled={busy} onClick={() => setMode("take_over")}>
            <HandPalm size={14} /> Take over
          </Button>
        </div>
      ) : (
        <div className="mt-4">
          <textarea
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={3}
            placeholder={
              mode === "modify"
                ? "Corrected output to use instead…"
                : "Provide the output yourself; the agents stand down…"
            }
            className="w-full resize-none rounded-md bg-canvas/60 p-2.5 text-[13px] text-ink outline-none placeholder:text-faint"
          />
          <div className="mt-2 flex gap-2">
            <Button variant="primary" size="sm" disabled={busy || !draft.trim()} onClick={() => resolve(mode, draft)}>
              Submit {mode === "modify" ? "correction" : "output"}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setMode(null)}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Chat panel */}
      <div className="mt-4 border-t border-hairline-soft pt-3">
        {chat.length > 0 && (
          <div className="mb-2 space-y-1.5">
            {chat.map((t, i) => (
              <div key={i} className="text-[12px]">
                <span className={t.role === "human" ? "text-ink" : "text-muted"}>
                  <span className="font-medium">
                    {t.role === "human" ? "You" : "Agent"}:
                  </span>{" "}
                  {t.text}
                </span>
              </div>
            ))}
          </div>
        )}
        <div className="flex items-center gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            placeholder="Ask the agent before deciding…"
            className="h-8 flex-1 rounded-md bg-canvas/60 px-2.5 text-[13px] text-ink outline-none placeholder:text-faint"
          />
          <Button variant="secondary" size="icon" disabled={asking || !question.trim()} onClick={ask}>
            <PaperPlaneRight size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
}

export function ReviewQueueApp() {
  const [approvals, setApprovals] = useState<ApprovalFull[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback((signal?: AbortSignal) => {
    getApprovals(signal)
      .then((a) => {
        setApprovals(a);
        setError(null);
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
    const id = setInterval(() => load(), 2000);
    return () => {
      ctrl.abort();
      clearInterval(id);
    };
  }, [load]);

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

  if (!approvals || approvals.length === 0) {
    return (
      <div className="px-5 py-5">
        <EmptyState
          icon={ShieldCheck}
          title="No escalations waiting"
          description="When a run's confidence drops or the reviewer rejects output twice, it pauses here for your decision. Run a task in New Task to see it in action."
        />
      </div>
    );
  }

  return (
    <div className="space-y-3 px-5 py-5">
      <p className="text-[13px] text-muted">
        {approvals.length} run{approvals.length > 1 ? "s" : ""} paused, waiting on you.
      </p>
      {approvals.map((a) => (
        <ApprovalCard key={a.id} approval={a} onResolved={() => load()} />
      ))}
    </div>
  );
}
