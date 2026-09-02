import Link from "next/link";
import { Compass } from "@phosphor-icons/react/dist/ssr";
import { Button } from "@/components/ui/button";

/** Custom 404 in the design system (design-guardrails §B, fix #8). */
export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center text-center">
      <span className="mb-5 grid h-12 w-12 place-items-center rounded-card border border-hairline bg-surface text-faint">
        <Compass size={22} />
      </span>
      <p className="font-mono text-[12px] uppercase tracking-widest text-accent">
        404
      </p>
      <h1 className="mt-2 font-display text-xl font-semibold text-ink">
        This route isn&apos;t on the map
      </h1>
      <p className="mt-2 text-[13px] leading-relaxed text-muted">
        The page you&apos;re after doesn&apos;t exist, or it hasn&apos;t been
        built yet. Head back to the command center to pick up a task.
      </p>
      <Link href="/" className="mt-6">
        <Button variant="primary" size="md">
          Back to Command Center
        </Button>
      </Link>
    </div>
  );
}
