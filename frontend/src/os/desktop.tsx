"use client";

import { useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { useOS } from "./store";
import { MenuBar } from "./menu-bar";
import { Dock } from "./dock";
import { Window } from "./window";
import { Spotlight } from "./spotlight";

const WALLPAPER =
  "radial-gradient(1100px 640px at 14% 8%, rgba(126,138,158,0.22), transparent 62%)," +
  "radial-gradient(1000px 720px at 88% 96%, rgba(158,118,96,0.20), transparent 60%)," +
  "linear-gradient(158deg, #2b2a30 0%, #1b1a18 56%, #121110 100%)";

export function Desktop() {
  const windows = useOS((s) => s.windows);
  const openApp = useOS((s) => s.openApp);

  // Boot with the Command Center open.
  useEffect(() => {
    if (useOS.getState().windows.length === 0) openApp("command");
  }, [openApp]);

  return (
    <div
      className="relative h-screen w-screen overflow-hidden"
      style={{ background: WALLPAPER }}
    >
      <MenuBar />

      <div className="absolute inset-0 pt-7">
        <AnimatePresence>
          {windows
            .filter((w) => !w.minimized)
            .map((win) => (
              <Window key={win.id} win={win} />
            ))}
        </AnimatePresence>
      </div>

      <Dock />
      <Spotlight />
    </div>
  );
}
