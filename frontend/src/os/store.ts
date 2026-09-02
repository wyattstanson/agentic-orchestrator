import { create } from "zustand";
import { type AppId, getMeta } from "@/apps/meta";

export type WindowState = {
  id: string;
  appId: AppId;
  x: number;
  y: number;
  w: number;
  h: number;
  z: number;
  minimized: boolean;
  maximized: boolean;
  /** Saved geometry to restore from a maximized state. */
  restore?: { x: number; y: number; w: number; h: number };
};

type OSState = {
  windows: WindowState[];
  topZ: number;
  focusedId: string | null;
  spotlightOpen: boolean;

  openApp: (appId: AppId) => void;
  close: (id: string) => void;
  focus: (id: string) => void;
  minimize: (id: string) => void;
  toggleMaximize: (id: string) => void;
  move: (id: string, x: number, y: number) => void;
  resize: (id: string, w: number, h: number) => void;
  setSpotlight: (open: boolean) => void;
};

let counter = 0;
const nextId = () => `win-${++counter}`;

export const useOS = create<OSState>((set, get) => ({
  windows: [],
  topZ: 1,
  focusedId: null,
  spotlightOpen: false,

  openApp: (appId) => {
    const { windows, topZ } = get();
    // Apps are single-window: focus/restore if already open.
    const existing = windows.find((w) => w.appId === appId);
    if (existing) {
      get().focus(existing.id);
      return;
    }
    const meta = getMeta(appId);
    const openCount = windows.length;
    const z = topZ + 1;
    const win: WindowState = {
      id: nextId(),
      appId,
      x: 130 + openCount * 26,
      y: 84 + openCount * 26,
      w: meta.w,
      h: meta.h,
      z,
      minimized: false,
      maximized: false,
    };
    set({ windows: [...windows, win], topZ: z, focusedId: win.id });
  },

  close: (id) =>
    set((s) => ({ windows: s.windows.filter((w) => w.id !== id) })),

  focus: (id) =>
    set((s) => {
      const z = s.topZ + 1;
      return {
        topZ: z,
        focusedId: id,
        windows: s.windows.map((w) =>
          w.id === id ? { ...w, z, minimized: false } : w,
        ),
      };
    }),

  minimize: (id) =>
    set((s) => ({
      windows: s.windows.map((w) =>
        w.id === id ? { ...w, minimized: true } : w,
      ),
      focusedId: s.focusedId === id ? null : s.focusedId,
    })),

  toggleMaximize: (id) =>
    set((s) => ({
      windows: s.windows.map((w) => {
        if (w.id !== id) return w;
        if (w.maximized && w.restore) {
          return { ...w, maximized: false, ...w.restore, restore: undefined };
        }
        return {
          ...w,
          maximized: true,
          restore: { x: w.x, y: w.y, w: w.w, h: w.h },
        };
      }),
    })),

  move: (id, x, y) =>
    set((s) => ({
      windows: s.windows.map((w) => (w.id === id ? { ...w, x, y } : w)),
    })),

  resize: (id, w, h) =>
    set((s) => ({
      windows: s.windows.map((win) =>
        win.id === id
          ? { ...win, w: Math.max(360, w), h: Math.max(280, h) }
          : win,
      ),
    })),

  setSpotlight: (open) => set({ spotlightOpen: open }),
}));
