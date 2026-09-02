"use client";

import { useRef } from "react";
import { motion } from "framer-motion";
import { X, Minus, ArrowsOut } from "@phosphor-icons/react/dist/ssr";
import { getApp } from "@/apps/registry";
import { useOS, type WindowState } from "./store";
import { cn } from "@/lib/utils";

const MENUBAR_H = 28;

export function Window({ win }: { win: WindowState }) {
  const { focus, close, minimize, toggleMaximize, move, resize } = useOS();
  const app = getApp(win.appId);
  const dragState = useRef<{ dx: number; dy: number } | null>(null);
  const resizeState = useRef<{ sx: number; sy: number; w: number; h: number } | null>(null);

  function onHeaderPointerDown(e: React.PointerEvent) {
    if (win.maximized) return;
    if ((e.target as HTMLElement).closest("[data-no-drag]")) return;
    focus(win.id);
    dragState.current = { dx: e.clientX - win.x, dy: e.clientY - win.y };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }
  function onHeaderPointerMove(e: React.PointerEvent) {
    if (!dragState.current) return;
    const y = Math.max(MENUBAR_H, e.clientY - dragState.current.dy);
    move(win.id, e.clientX - dragState.current.dx, y);
  }
  function endDrag(e: React.PointerEvent) {
    dragState.current = null;
    try {
      (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      /* pointer already released */
    }
  }

  function onResizePointerDown(e: React.PointerEvent) {
    e.stopPropagation();
    focus(win.id);
    resizeState.current = { sx: e.clientX, sy: e.clientY, w: win.w, h: win.h };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }
  function onResizePointerMove(e: React.PointerEvent) {
    const r = resizeState.current;
    if (!r) return;
    resize(win.id, r.w + (e.clientX - r.sx), r.h + (e.clientY - r.sy));
  }

  const geometry = win.maximized
    ? { left: 8, top: MENUBAR_H + 6, width: "calc(100vw - 16px)", height: "calc(100vh - 120px)" }
    : { left: win.x, top: win.y, width: win.w, height: win.h };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ type: "spring", stiffness: 460, damping: 34 }}
      style={{ ...geometry, zIndex: win.z }}
      onPointerDown={() => focus(win.id)}
      className="absolute flex flex-col overflow-hidden rounded-[12px] border border-hairline bg-surface shadow-[0_24px_70px_-18px_rgba(0,0,0,0.45),0_6px_18px_-8px_rgba(0,0,0,0.28)]"
    >
      {/* Title bar */}
      <div
        onPointerDown={onHeaderPointerDown}
        onPointerMove={onHeaderPointerMove}
        onPointerUp={endDrag}
        onDoubleClick={() => toggleMaximize(win.id)}
        className="relative flex h-9 shrink-0 items-center border-b border-hairline-soft bg-surface px-3 select-none"
      >
        {/* Custom window controls — graphite dots, glyphs on hover */}
        <div className="group/tl flex items-center gap-2" data-no-drag>
          <button
            aria-label="Close"
            onClick={() => close(win.id)}
            className="grid h-3 w-3 place-items-center rounded-full bg-ink/20 text-transparent transition-colors hover:bg-attention hover:text-white"
          >
            <X size={8} weight="bold" className="opacity-0 group-hover/tl:opacity-100" />
          </button>
          <button
            aria-label="Minimize"
            onClick={() => minimize(win.id)}
            className="grid h-3 w-3 place-items-center rounded-full bg-ink/20 text-transparent transition-colors hover:bg-ink/40 hover:text-ink"
          >
            <Minus size={8} weight="bold" className="opacity-0 group-hover/tl:opacity-100" />
          </button>
          <button
            aria-label="Maximize"
            onClick={() => toggleMaximize(win.id)}
            className="grid h-3 w-3 place-items-center rounded-full bg-ink/20 text-transparent transition-colors hover:bg-ink/40 hover:text-ink"
          >
            <ArrowsOut size={7} weight="bold" className="opacity-0 group-hover/tl:opacity-100" />
          </button>
        </div>

        <span className="pointer-events-none absolute left-1/2 -translate-x-1/2 text-[13px] font-medium text-muted">
          {app.title}
        </span>
      </div>

      {/* Content */}
      <div className="min-h-0 flex-1 overflow-auto bg-surface">{app.render()}</div>

      {/* Resize handle */}
      {!win.maximized && (
        <div
          onPointerDown={onResizePointerDown}
          onPointerMove={onResizePointerMove}
          onPointerUp={endDrag}
          className="absolute bottom-0 right-0 h-4 w-4 cursor-se-resize"
          data-no-drag
        />
      )}
    </motion.div>
  );
}
