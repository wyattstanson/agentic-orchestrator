"use client";

import { MagnifyingGlass, SlidersHorizontal, WifiHigh } from "@phosphor-icons/react/dist/ssr";
import { getMeta } from "@/apps/meta";
import { useOS } from "./store";
import { Clock } from "./clock";

/** Small brand mark — the constellation glyph, no third-party logo. */
function Mark() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M8 8L3.5 4.5M8 8l4.5-3M8 8v4.5"
        stroke="white"
        strokeWidth="1.1"
        strokeLinecap="round"
        opacity="0.7"
      />
      <circle cx="8" cy="8" r="2.1" fill="white" />
      <circle cx="3.2" cy="4.2" r="1.35" fill="white" />
      <circle cx="12.8" cy="5" r="1.35" fill="white" />
      <circle cx="8" cy="13" r="1.35" fill="white" />
    </svg>
  );
}

export function MenuBar() {
  const focusedId = useOS((s) => s.focusedId);
  const windows = useOS((s) => s.windows);
  const setSpotlight = useOS((s) => s.setSpotlight);

  const focused = windows.find((w) => w.id === focusedId && !w.minimized);
  const activeName = focused ? getMeta(focused.appId).title : "Orchestrator";

  return (
    <header className="fixed inset-x-0 top-0 z-[9500] flex h-7 items-center gap-4 bg-black/35 px-3 text-[13px] text-white/85 backdrop-blur-xl">
      <div className="flex items-center gap-1.5">
        <Mark />
      </div>
      <span className="font-semibold text-white">{activeName}</span>

      <div className="ml-auto flex items-center gap-3.5">
        <WifiHigh size={15} className="hidden text-white/80 sm:block" />
        <button
          aria-label="Control center"
          className="text-white/80 transition-colors hover:text-white"
        >
          <SlidersHorizontal size={15} />
        </button>
        <button
          aria-label="Spotlight search"
          onClick={() => setSpotlight(true)}
          className="text-white/80 transition-colors hover:text-white"
        >
          <MagnifyingGlass size={15} />
        </button>
        <Clock />
      </div>
    </header>
  );
}
