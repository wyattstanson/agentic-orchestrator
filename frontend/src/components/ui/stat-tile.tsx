import { cn } from "@/lib/utils";
import { Card } from "./card";

/**
 * A single KPI readout. Values render in mono (instrument-readout feel,
 * master-build-prompt §7.2). Delta is optional and semantic-coloured.
 */
export function StatTile({
  label,
  value,
  unit,
  delta,
  deltaTone = "neutral",
}: {
  label: string;
  value: string;
  unit?: string;
  delta?: string;
  deltaTone?: "up" | "down" | "neutral";
}) {
  return (
    <Card className="px-5 py-4">
      <p className="text-[12px] font-medium text-muted">{label}</p>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold tabular-nums tracking-tight text-ink">
          {value}
        </span>
        {unit && <span className="text-[13px] text-muted">{unit}</span>}
      </div>
      {delta && (
        <p
          className={cn(
            "mt-1.5 text-[12px]",
            deltaTone === "up" && "text-success",
            deltaTone === "down" && "text-danger",
            deltaTone === "neutral" && "text-faint",
          )}
        >
          {delta}
        </p>
      )}
    </Card>
  );
}
