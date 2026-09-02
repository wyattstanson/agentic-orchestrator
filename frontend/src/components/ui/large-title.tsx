import { cn } from "@/lib/utils";

/** macOS "large title" page header: big semibold title, quiet subtitle. */
export function LargeTitle({
  title,
  subtitle,
  actions,
  className,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 pb-7 pt-1 sm:flex-row sm:items-end sm:justify-between",
        className,
      )}
    >
      <div>
        <h1 className="text-[26px] font-semibold leading-tight tracking-[-0.02em] text-ink">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 max-w-xl text-[13px] leading-relaxed text-muted">
            {subtitle}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex shrink-0 items-center gap-2">{actions}</div>
      )}
    </div>
  );
}
