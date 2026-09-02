"use client";

import { useMemo } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  type AgentNode,
  type AgentStatus,
  type ConstellationState,
} from "./types";
import { useDemoConstellation } from "./use-demo-constellation";
import { cn } from "@/lib/utils";

const VIEW_W = 680;
const VIEW_H = 460;
const CENTER = { x: VIEW_W / 2, y: VIEW_H / 2 };
const RX = 252;
const RY = 158;

type Point = { x: number; y: number };

/** Deterministic layout: supervisor centred, the rest on an ellipse. */
function layout(nodes: AgentNode[]): Map<string, Point> {
  const satellites = nodes.filter((n) => n.role !== "supervisor");
  const map = new Map<string, Point>();
  nodes
    .filter((n) => n.role === "supervisor")
    .forEach((n) => map.set(n.id, { ...CENTER }));

  const n = satellites.length;
  satellites.forEach((node, i) => {
    // Start at the top and go clockwise.
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    map.set(node.id, {
      x: CENTER.x + Math.cos(angle) * RX,
      y: CENTER.y + Math.sin(angle) * RY,
    });
  });
  return map;
}

const STATUS_RING: Record<AgentStatus, string> = {
  idle: "var(--hairline)",
  active: "var(--accent)",
  done: "color-mix(in srgb, var(--accent) 45%, var(--hairline))",
  failed: "var(--danger)",
};

const STATUS_LABEL: Record<AgentStatus, string> = {
  idle: "text-faint",
  active: "text-ink",
  done: "text-muted",
  failed: "text-danger",
};

function Particle({
  from,
  to,
  delay,
}: {
  from: Point;
  to: Point;
  delay: number;
}) {
  return (
    <motion.circle
      r={2.5}
      fill="var(--accent)"
      initial={{ cx: from.x, cy: from.y, opacity: 0 }}
      animate={{
        cx: [from.x, to.x],
        cy: [from.y, to.y],
        opacity: [0, 1, 1, 0],
      }}
      transition={{
        duration: 1.15,
        delay,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />
  );
}

export function AgentConstellation({
  state,
  className,
}: {
  state?: ConstellationState;
  className?: string;
}) {
  const demo = useDemoConstellation();
  const { nodes, edges } = state ?? demo;
  const reduce = useReducedMotion();
  const pos = useMemo(() => layout(nodes), [nodes]);

  return (
    <div className={cn("relative w-full", className)}>
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        className="h-auto w-full"
        role="img"
        aria-label="Live agent hierarchy: supervisor, specialists, and reviewer"
      >
        {/* Edges */}
        {edges.map((edge) => {
          const a = pos.get(edge.from);
          const b = pos.get(edge.to);
          if (!a || !b) return null;
          return (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={edge.active ? "var(--accent)" : "var(--hairline)"}
              strokeOpacity={edge.active ? 0.5 : 1}
              strokeWidth={1}
            />
          );
        })}

        {/* Particles on active edges (skipped under reduced-motion) */}
        {!reduce &&
          edges
            .filter((e) => e.active)
            .map((edge) => {
              const a = pos.get(edge.from);
              const b = pos.get(edge.to);
              if (!a || !b) return null;
              return (
                <g key={`p-${edge.from}-${edge.to}`}>
                  <Particle from={a} to={b} delay={0} />
                  <Particle from={a} to={b} delay={0.55} />
                </g>
              );
            })}

        {/* Nodes */}
        {nodes.map((node) => {
          const p = pos.get(node.id);
          if (!p) return null;
          const isSup = node.role === "supervisor";
          const r = isSup ? 30 : 22;

          return (
            <g key={node.id}>
              {/* Active node: a quiet expanding outline pulse — no glow. */}
              {node.status === "active" && !reduce && (
                <motion.circle
                  cx={p.x}
                  cy={p.y}
                  r={r}
                  fill="none"
                  stroke="var(--ink)"
                  strokeWidth={1}
                  initial={{ opacity: 0.35, scale: 1 }}
                  animate={{ opacity: [0.32, 0, 0.32], scale: [1, 1.55, 1] }}
                  transition={{ duration: 2.4, repeat: Infinity, ease: "easeOut" }}
                  style={{ transformOrigin: `${p.x}px ${p.y}px` }}
                />
              )}

              <motion.circle
                cx={p.x}
                cy={p.y}
                r={r}
                fill="var(--surface)"
                stroke={STATUS_RING[node.status]}
                strokeWidth={node.status === "idle" ? 1 : 1.5}
                initial={false}
                animate={
                  node.status === "failed" && !reduce
                    ? { stroke: ["var(--danger)", "var(--danger)", "color-mix(in srgb, var(--danger) 55%, var(--hairline))"] }
                    : {}
                }
                transition={{ duration: 0.7 }}
              />

              {/* Role dot in the centre */}
              <circle
                cx={p.x}
                cy={p.y}
                r={isSup ? 5 : 4}
                fill={
                  node.status === "active"
                    ? "var(--ink)"
                    : node.status === "failed"
                      ? "var(--attention)"
                      : "var(--faint)"
                }
              />

              <text
                x={p.x}
                y={p.y + r + 16}
                textAnchor="middle"
                className={cn(
                  "text-[11px] font-medium",
                  STATUS_LABEL[node.status],
                )}
                fill="currentColor"
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
