import { cn } from "@/lib/utils";

type Status = "running" | "escalated" | "done" | "failed" | "idle";

// Near-monochrome: ink shades carry most states; the single attention colour
// appears only where the operator is actually needed.
const COLOR: Record<Status, string> = {
  running: "bg-ink",
  done: "bg-faint",
  idle: "bg-faint/50",
  escalated: "bg-attention",
  failed: "bg-attention",
};

export function StatusDot({
  status,
  className,
}: {
  status: Status;
  className?: string;
}) {
  return (
    <span className={cn("relative inline-flex h-[7px] w-[7px]", className)}>
      {status === "running" && (
        <span className="absolute inset-0 animate-ping rounded-full bg-ink/25" />
      )}
      <span className={cn("relative h-[7px] w-[7px] rounded-full", COLOR[status])} />
    </span>
  );
}
