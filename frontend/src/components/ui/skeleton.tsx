import { cn } from "@/lib/utils";

/**
 * Content-shaped skeleton (design-guardrails §A.21 requires these, never a
 * spinner). The shimmer is a CSS animation, so prefers-reduced-motion halts it.
 */
export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-control bg-hairline-soft",
        "before:absolute before:inset-0 before:-translate-x-full",
        "before:animate-[shimmer_1.6s_infinite]",
        "before:bg-gradient-to-r before:from-transparent before:via-hairline before:to-transparent",
        className,
      )}
      {...props}
    />
  );
}
