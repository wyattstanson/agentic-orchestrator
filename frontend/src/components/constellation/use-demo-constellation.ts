"use client";

import { useEffect, useState } from "react";
import {
  type ConstellationState,
  DEFAULT_EDGES,
  DEFAULT_NODES,
} from "./types";

/**
 * A self-driving demo of a task moving through the hierarchy, used until the
 * backend streams real execution state in a later phase. Sequence: supervisor
 * plans, each specialist runs in turn (one deliberately fails then recovers),
 * the reviewer grades, then the run settles.
 */
const SEQUENCE: { active: string; fail?: boolean }[] = [
  { active: "supervisor" },
  { active: "research" },
  { active: "data" },
  { active: "code", fail: true },
  { active: "code" },
  { active: "writing" },
  { active: "reviewer" },
];

export function useDemoConstellation(): ConstellationState {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setStep((s) => (s + 1) % (SEQUENCE.length + 2)), 1900);
    return () => clearInterval(id);
  }, []);

  const nodes = DEFAULT_NODES.map((node) => {
    // Steps beyond the sequence = a settled, all-done run before it loops.
    if (step >= SEQUENCE.length) {
      return { ...node, status: "done" as const };
    }
    const current = SEQUENCE[step];
    const currentIndex = SEQUENCE.findIndex((s) => s.active === node.id);

    if (current.active === node.id) {
      return { ...node, status: current.fail ? ("failed" as const) : ("active" as const) };
    }
    // Anything whose turn already passed is done.
    if (currentIndex !== -1 && currentIndex < step) {
      return { ...node, status: "done" as const };
    }
    return { ...node, status: "idle" as const };
  });

  const activeId = step < SEQUENCE.length ? SEQUENCE[step].active : null;
  const edges = DEFAULT_EDGES.map((edge) => ({
    ...edge,
    active: activeId !== null && (edge.to === activeId || edge.from === activeId),
  }));

  return { nodes, edges };
}
