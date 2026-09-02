import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "success";
type Size = "sm" | "md" | "lg" | "icon";

const VARIANTS: Record<Variant, string> = {
  // The one accent, used with restraint for primary actions.
  primary:
    "bg-accent text-on-accent hover:bg-accent-hover disabled:bg-accent/50",
  secondary:
    "bg-surface text-ink border border-hairline hover:border-faint hover:bg-elevated",
  ghost: "bg-transparent text-muted hover:bg-accent-soft hover:text-ink",
  danger:
    "bg-transparent text-danger border border-danger/40 hover:bg-danger/10",
  success:
    "bg-success text-white hover:brightness-110 disabled:bg-success/50",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px] gap-1.5",
  md: "h-9 px-4 text-sm gap-2",
  lg: "h-11 px-5 text-[15px] gap-2",
  icon: "h-9 w-9 justify-center",
};

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

/**
 * Design-system button. Hover changes colour only — no lift/scale/tilt
 * (design-guardrails §A.28: functional hovers only).
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "secondary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-control font-medium",
        "transition-colors duration-150 ease-out",
        "disabled:cursor-not-allowed disabled:opacity-60",
        "focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-2",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
