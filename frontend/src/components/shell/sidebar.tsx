"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { NAV_GROUPS } from "@/lib/nav";
import { cn } from "@/lib/utils";

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** Small mark: a supervisor node linked to two satellites (not a stock icon). */
function LogoMark() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M8 8L3.5 4.5M8 8l4.5-3M8 8v4.5"
        stroke="var(--accent)"
        strokeWidth="1.1"
        strokeLinecap="round"
        opacity="0.6"
      />
      <circle cx="8" cy="8" r="2.1" fill="var(--accent)" />
      <circle cx="3.2" cy="4.2" r="1.35" fill="var(--accent)" />
      <circle cx="12.8" cy="5" r="1.35" fill="var(--accent)" />
      <circle cx="8" cy="13" r="1.35" fill="var(--accent)" />
    </svg>
  );
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-[236px] shrink-0 flex-col border-r border-hairline bg-surface/60 backdrop-blur-2xl md:flex">
      <Link
        href="/"
        className="flex h-[52px] items-center gap-2 px-4 focus-visible:outline-none"
      >
        <LogoMark />
        <span className="text-[13px] font-semibold tracking-tight text-ink">
          Orchestrator
        </span>
      </Link>

      <nav className="flex-1 overflow-y-auto px-2.5 pb-4">
        {NAV_GROUPS.map((group) => (
          <div key={group.title} className="mb-4">
            <p className="px-2 pb-1 text-[11px] font-semibold text-faint">
              {group.title}
            </p>
            <div className="space-y-px">
              {group.items.map((item) => {
                const active = isActive(pathname, item.href);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "relative flex h-7 items-center gap-2.5 rounded-md px-2 text-[13px] transition-colors",
                      active
                        ? "text-ink"
                        : "text-muted hover:bg-ink/[0.035] hover:text-ink",
                    )}
                  >
                    {active && (
                      <motion.span
                        layoutId="nav-active"
                        className="absolute inset-0 rounded-md bg-ink/[0.06]"
                        transition={{ type: "spring", stiffness: 500, damping: 40 }}
                      />
                    )}
                    <Icon
                      size={16}
                      weight="regular"
                      className={cn(
                        "relative z-10 shrink-0",
                        active ? "text-accent" : "text-faint",
                      )}
                    />
                    <span
                      className={cn(
                        "relative z-10 truncate",
                        active && "font-medium",
                      )}
                    >
                      {item.label}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
