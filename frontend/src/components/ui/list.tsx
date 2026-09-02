import * as React from "react";
import { cn } from "@/lib/utils";

/** A titled section wrapping one grouped list (macOS System Settings pattern). */
export function ListSection({
  title,
  trailing,
  children,
  className,
}: {
  title?: string;
  trailing?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("mb-7", className)}>
      {(title || trailing) && (
        <div className="mb-2 flex items-center justify-between px-1">
          {title && (
            <h2 className="text-[13px] font-semibold text-muted">{title}</h2>
          )}
          {trailing}
        </div>
      )}
      {children}
    </section>
  );
}

/** Rounded, inset, soft-shadowed container with hairline-divided rows. */
export function ListGroup({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-card bg-surface",
        "divide-y divide-hairline-soft",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** One list row: leading slot, title/subtitle stack, trailing slot. */
export function ListRow({
  leading,
  title,
  subtitle,
  trailing,
  onClick,
  className,
}: {
  leading?: React.ReactNode;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  trailing?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  const interactive = Boolean(onClick);
  return (
    <div
      onClick={onClick}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      className={cn(
        "flex items-center gap-3 px-4 py-2.5",
        interactive && "cursor-pointer transition-colors hover:bg-ink/[0.025]",
        className,
      )}
    >
      {leading && <div className="flex shrink-0 items-center">{leading}</div>}
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13px] text-ink">{title}</div>
        {subtitle && (
          <div className="mt-0.5 truncate text-[12px] text-faint">{subtitle}</div>
        )}
      </div>
      {trailing && (
        <div className="flex shrink-0 items-center gap-3">{trailing}</div>
      )}
    </div>
  );
}
