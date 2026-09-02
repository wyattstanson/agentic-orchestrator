import { cn } from "@/lib/utils";

/** Lead description + optional actions under the topbar title. */
export function PageIntro({
  description,
  actions,
  className,
}: {
  description: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <p className="max-w-2xl text-[13px] leading-relaxed text-muted">
        {description}
      </p>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
