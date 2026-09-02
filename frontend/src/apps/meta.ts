export type AppId =
  | "command"
  | "tasks"
  | "review"
  | "trace"
  | "memory"
  | "analytics"
  | "replay"
  | "tools";

export type AppMeta = {
  id: AppId;
  title: string;
  /** Default window size on first open. */
  w: number;
  h: number;
  /** Dock grouping — a thin divider is drawn between groups. */
  group: 1 | 2 | 3;
};

export const APP_METAS: AppMeta[] = [
  { id: "command", title: "Command Center", w: 780, h: 580, group: 1 },
  { id: "tasks", title: "New Task", w: 640, h: 480, group: 1 },
  { id: "review", title: "Review Queue", w: 660, h: 500, group: 1 },
  { id: "trace", title: "Trace Explorer", w: 720, h: 520, group: 2 },
  { id: "memory", title: "Memory", w: 680, h: 500, group: 2 },
  { id: "analytics", title: "Analytics", w: 700, h: 500, group: 2 },
  { id: "replay", title: "Replay", w: 700, h: 500, group: 2 },
  { id: "tools", title: "Tool Registry", w: 700, h: 500, group: 3 },
];

export function getMeta(id: AppId): AppMeta {
  const m = APP_METAS.find((a) => a.id === id);
  if (!m) throw new Error(`Unknown app: ${id}`);
  return m;
}
