"use client";

import { MagnifyingGlass, List } from "@phosphor-icons/react/dist/ssr";
import { ThemeToggle } from "./theme-toggle";

export function Topbar({ onOpenPalette }: { onOpenPalette: () => void }) {
  return (
    <header className="sticky top-0 z-30 flex h-[52px] items-center gap-3 border-b border-hairline bg-surface/60 px-4 backdrop-blur-2xl">
      <button
        type="button"
        aria-label="Open menu"
        className="grid h-7 w-7 place-items-center rounded-md text-muted transition-colors hover:bg-ink/[0.05] hover:text-ink md:hidden"
      >
        <List size={17} />
      </button>

      <div className="ml-auto flex items-center gap-2">
        <button
          type="button"
          onClick={onOpenPalette}
          aria-label="Search"
          className="flex h-7 w-44 items-center gap-2 rounded-md bg-ink/[0.05] px-2.5 text-[13px] text-faint transition-colors hover:bg-ink/[0.07]"
        >
          <MagnifyingGlass size={14} />
          <span>Search</span>
          <kbd className="ml-auto font-sans text-[11px] text-faint">⌘K</kbd>
        </button>
        <ThemeToggle />
      </div>
    </header>
  );
}
