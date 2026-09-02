"use client";

import { useRef } from "react";
import {
  motion,
  useMotionValue,
  useSpring,
  useTransform,
  type MotionValue,
} from "framer-motion";
import type { Icon } from "@phosphor-icons/react";
import { APP_LIST, APP_COLORS, type AppEntry } from "@/apps/registry";
import { getMeta } from "@/apps/meta";
import { useOS } from "./store";

function DockIcon({
  app,
  mouseX,
  isOpen,
  onClick,
}: {
  app: AppEntry;
  mouseX: MotionValue<number>;
  isOpen: boolean;
  onClick: () => void;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const Glyph: Icon = app.icon;

  const distance = useTransform(mouseX, (val) => {
    const b = ref.current?.getBoundingClientRect();
    const center = b ? b.x + b.width / 2 : 0;
    return val - center;
  });
  const scaleT = useTransform(distance, [-130, 0, 130], [1, 1.5, 1]);
  const scale = useSpring(scaleT, { stiffness: 320, damping: 20, mass: 0.15 });

  return (
    <button
      ref={ref}
      onClick={onClick}
      aria-label={app.title}
      className="group/icon relative flex flex-col items-center"
    >
      {/* Hover label */}
      <span className="pointer-events-none absolute -top-9 whitespace-nowrap rounded-md bg-[#111]/85 px-2 py-1 text-[11px] text-white opacity-0 backdrop-blur transition-opacity group-hover/icon:opacity-100">
        {app.title}
      </span>

      <motion.span
        style={{
          scale,
          backgroundImage: `linear-gradient(to bottom, ${APP_COLORS[app.id][0]}, ${APP_COLORS[app.id][1]})`,
        }}
        className="grid h-[46px] w-[46px] origin-bottom place-items-center rounded-[13px] border border-white/15 text-white shadow-[0_4px_10px_-3px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.18)]"
      >
        <Glyph size={22} weight="regular" />
      </motion.span>

      {/* Running indicator */}
      <span
        className={`mt-1 h-[3px] w-[3px] rounded-full transition-colors ${
          isOpen ? "bg-white/70" : "bg-transparent"
        }`}
      />
    </button>
  );
}

export function Dock() {
  const mouseX = useMotionValue(Infinity);
  const openApp = useOS((s) => s.openApp);
  const windows = useOS((s) => s.windows);
  const openIds = new Set(windows.map((w) => w.appId));

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-2 z-[9000] flex justify-center">
      <div
        onMouseMove={(e) => mouseX.set(e.clientX)}
        onMouseLeave={() => mouseX.set(Infinity)}
        className="pointer-events-auto flex items-end gap-2.5 rounded-2xl border border-white/10 bg-white/10 px-2.5 pb-2 pt-2.5 backdrop-blur-2xl"
        style={{ boxShadow: "0 12px 40px -8px rgba(0,0,0,0.45)" }}
      >
        {APP_LIST.map((app, i) => {
          const prev = APP_LIST[i - 1];
          const showDivider = prev && getMeta(prev.id).group !== getMeta(app.id).group;
          return (
            <div key={app.id} className="flex items-end gap-2.5">
              {showDivider && <div className="mb-1 h-9 w-px self-center bg-white/15" />}
              <DockIcon
                app={app}
                mouseX={mouseX}
                isOpen={openIds.has(app.id)}
                onClick={() => openApp(app.id)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
