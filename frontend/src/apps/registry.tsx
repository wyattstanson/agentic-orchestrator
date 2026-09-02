"use client";

import type { ReactNode } from "react";
import type { Icon } from "@phosphor-icons/react";
import {
  House,
  PlusCircle,
  Bell,
  TreeStructure,
  Brain,
  ChartBar,
  ClockCounterClockwise,
  Wrench,
} from "@phosphor-icons/react/dist/ssr";
import { type AppId, APP_METAS, getMeta } from "./meta";
import { CommandCenterApp } from "./views/command-center-app";
import { NewTaskApp } from "./views/new-task-app";
import { ToolRegistryApp } from "./views/tool-registry-app";
import { MemoryApp } from "./views/memory-app";
import { ReviewQueueApp } from "./views/review-queue-app";
import { TraceExplorerApp } from "./views/trace-explorer-app";
import { AnalyticsApp } from "./views/analytics-app";
import { ReplayApp } from "./views/replay-app";

export type AppEntry = {
  id: AppId;
  title: string;
  icon: Icon;
  render: () => ReactNode;
};

const ICONS: Record<AppId, Icon> = {
  command: House,
  tasks: PlusCircle,
  review: Bell,
  trace: TreeStructure,
  memory: Brain,
  analytics: ChartBar,
  replay: ClockCounterClockwise,
  tools: Wrench,
};

/** Muted, desaturated dock-icon gradients [top, bottom] — a bit of colour. */
export const APP_COLORS: Record<AppId, [string, string]> = {
  command: ["#5b7aa8", "#405d86"],
  tasks: ["#4f9a8b", "#377167"],
  review: ["#c39a52", "#a07636"],
  trace: ["#6f9a5b", "#527540"],
  memory: ["#8f6aa0", "#6c4e7c"],
  analytics: ["#5a86b0", "#3f628a"],
  replay: ["#b06a4f", "#8a5039"],
  tools: ["#6c7176", "#4c5054"],
};

const RENDER: Record<AppId, () => ReactNode> = {
  command: () => <CommandCenterApp />,
  tasks: () => <NewTaskApp />,
  review: () => <ReviewQueueApp />,
  trace: () => <TraceExplorerApp />,
  memory: () => <MemoryApp />,
  analytics: () => <AnalyticsApp />,
  replay: () => <ReplayApp />,
  tools: () => <ToolRegistryApp />,
};

export const APP_LIST: AppEntry[] = APP_METAS.map((m) => ({
  id: m.id,
  title: m.title,
  icon: ICONS[m.id],
  render: RENDER[m.id],
}));

export function getApp(id: AppId): AppEntry {
  return {
    id,
    title: getMeta(id).title,
    icon: ICONS[id],
    render: RENDER[id],
  };
}
