"use client";

import { useEffect } from "react";
import { Command } from "cmdk";
import { AnimatePresence, motion } from "framer-motion";
import { APP_LIST, APP_COLORS } from "@/apps/registry";
import { getMeta } from "@/apps/meta";
import { useOS } from "./store";

export function Spotlight() {
  const open = useOS((s) => s.spotlightOpen);
  const setOpen = useOS((s) => s.setSpotlight);
  const openApp = useOS((s) => s.openApp);

  // Cmd/Ctrl+K and Escape.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(!useOS.getState().spotlightOpen);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setOpen]);

  function launch(id: Parameters<typeof openApp>[0]) {
    setOpen(false);
    openApp(id);
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[9800] flex items-start justify-center p-4 pt-[16vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.12 }}
        >
          <div className="absolute inset-0" onClick={() => setOpen(false)} />
          <motion.div
            className="relative w-full max-w-lg overflow-hidden rounded-[14px] border border-white/15 bg-[#1c1c1b]/80 backdrop-blur-2xl"
            style={{ boxShadow: "0 30px 80px -20px rgba(0,0,0,0.6)" }}
            initial={{ opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 420, damping: 30 }}
          >
            <Command
              className="w-full"
              filter={(value, search) =>
                value.toLowerCase().includes(search.toLowerCase()) ? 1 : 0
              }
            >
              <Command.Input
                autoFocus
                placeholder="Open an app…"
                className="w-full border-b border-white/10 bg-transparent px-4 py-3.5 text-[15px] text-white outline-none placeholder:text-white/40"
              />
              <Command.List className="max-h-80 overflow-y-auto p-2">
                <Command.Empty className="px-3 py-6 text-center text-[13px] text-white/40">
                  No app matches that.
                </Command.Empty>
                {APP_LIST.map((app) => {
                  const Glyph = app.icon;
                  return (
                    <Command.Item
                      key={app.id}
                      value={app.title}
                      onSelect={() => launch(app.id)}
                      className="flex cursor-pointer items-center gap-3 rounded-lg px-2.5 py-2 text-[13px] text-white/80 data-[selected=true]:bg-white/10 data-[selected=true]:text-white"
                    >
                      <span
                        className="grid h-7 w-7 place-items-center rounded-[8px] text-white"
                        style={{
                          backgroundImage: `linear-gradient(to bottom, ${APP_COLORS[app.id][0]}, ${APP_COLORS[app.id][1]})`,
                        }}
                      >
                        <Glyph size={16} />
                      </span>
                      <span>{app.title}</span>
                      <span className="ml-auto text-[11px] text-white/35">
                        {getMeta(app.id).w}×{getMeta(app.id).h}
                      </span>
                    </Command.Item>
                  );
                })}
              </Command.List>
            </Command>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
