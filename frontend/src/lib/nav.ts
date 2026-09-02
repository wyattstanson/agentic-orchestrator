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

export type NavItem = {
  label: string;
  href: string;
  icon: Icon;
  hint: string;
};

export type NavGroup = {
  title: string;
  items: NavItem[];
};

/** Source-list groups, Finder/Mail-style. */
export const NAV_GROUPS: NavGroup[] = [
  {
    title: "Operate",
    items: [
      { label: "Command Center", href: "/", icon: House, hint: "Active tasks and the live run" },
      { label: "New Task", href: "/tasks", icon: PlusCircle, hint: "Submit a request" },
      { label: "Review Queue", href: "/review", icon: Bell, hint: "Escalations waiting on you" },
    ],
  },
  {
    title: "Observe",
    items: [
      { label: "Trace Explorer", href: "/trace", icon: TreeStructure, hint: "Drill into a run's decision tree" },
      { label: "Memory", href: "/memory", icon: Brain, hint: "What the system remembers" },
      { label: "Analytics", href: "/analytics", icon: ChartBar, hint: "Cost and latency trends" },
      { label: "Replay", href: "/replay", icon: ClockCounterClockwise, hint: "Step through a past run" },
    ],
  },
  {
    title: "Configure",
    items: [
      { label: "Tool Registry", href: "/tools", icon: Wrench, hint: "Registered tools and limits" },
    ],
  },
];

/** Flat list for the command palette and title lookups. */
export const NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);
