"use client";

import type { Icon } from "@phosphor-icons/react";
import { EmptyState } from "@/components/ui/empty-state";

/** Shared content for screens whose backend lands in a later phase. */
export function PlaceholderApp({
  icon,
  subtitle,
  emptyTitle,
  emptyDescription,
}: {
  icon: Icon;
  subtitle: string;
  emptyTitle: string;
  emptyDescription: string;
}) {
  return (
    <div className="px-5 py-5">
      <p className="mb-5 text-[13px] leading-relaxed text-muted">{subtitle}</p>
      <EmptyState
        icon={icon}
        title={emptyTitle}
        description={emptyDescription}
      />
    </div>
  );
}
