import type { Icon } from "@phosphor-icons/react";
import { cn } from "@/lib/utils";

/**
 * Real empty state with a clear next action (design-guardrails §7.6),
 * never a bare "No data."
 */
export function EmptyState({
  icon: IconCmp,
  title,
  description,
  action,
  className,
}: {
  icon: Icon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-card border border-dashed border-hairline px-6 py-16 text-center",
        className,
      )}
    >
      <span className="mb-4 grid h-11 w-11 place-items-center rounded-card border border-hairline-soft bg-surface text-faint">
        <IconCmp size={20} />
      </span>
      <h3 className="font-display text-[15px] font-semibold text-ink">
        {title}
      </h3>
      <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-muted">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
