export type AgentStatus = "idle" | "active" | "done" | "failed";

export type AgentRole = "supervisor" | "specialist" | "reviewer";

export type AgentNode = {
  id: string;
  label: string;
  role: AgentRole;
  status: AgentStatus;
};

export type AgentEdge = {
  from: string;
  to: string;
  /** True while data is actively flowing from → to (drives particles). */
  active?: boolean;
};

export type ConstellationState = {
  nodes: AgentNode[];
  edges: AgentEdge[];
};

/** The default hierarchy: a supervisor, four specialists, one reviewer. */
export const DEFAULT_NODES: AgentNode[] = [
  { id: "supervisor", label: "Supervisor", role: "supervisor", status: "idle" },
  { id: "research", label: "Research", role: "specialist", status: "idle" },
  { id: "data", label: "Data / Analysis", role: "specialist", status: "idle" },
  { id: "writing", label: "Writing", role: "specialist", status: "idle" },
  { id: "code", label: "Code Exec", role: "specialist", status: "idle" },
  { id: "reviewer", label: "Reviewer", role: "reviewer", status: "idle" },
];

export const DEFAULT_EDGES: AgentEdge[] = [
  { from: "supervisor", to: "research" },
  { from: "supervisor", to: "data" },
  { from: "supervisor", to: "writing" },
  { from: "supervisor", to: "code" },
  { from: "supervisor", to: "reviewer" },
];
