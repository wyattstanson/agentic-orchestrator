"use client";

import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { AnimatePresence, motion } from "framer-motion";
import { NAV_ITEMS } from "@/lib/nav";

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();

  function go(href: string) {
    onOpenChange(false);
    router.push(href);
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-[12vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
        >
          <div
            className="absolute inset-0 bg-canvas/70 backdrop-blur-sm"
            onClick={() => onOpenChange(false)}
          />
          <motion.div
            className="glass relative w-full max-w-xl overflow-hidden rounded-modal"
            initial={{ opacity: 0, y: 8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ type: "spring", stiffness: 380, damping: 30 }}
          >
            <Command
              className="w-full"
              // Filter over label + hint text.
              filter={(value, search) =>
                value.toLowerCase().includes(search.toLowerCase()) ? 1 : 0
              }
            >
              <Command.Input
                autoFocus
                placeholder="Jump to a screen, task, or trace…"
                className="w-full border-b border-hairline-soft bg-transparent px-4 py-3.5 text-sm text-ink outline-none placeholder:text-faint"
              />
              <Command.List className="max-h-80 overflow-y-auto p-2">
                <Command.Empty className="px-3 py-6 text-center text-[13px] text-faint">
                  Nothing matches. Try a screen name like “trace” or “memory.”
                </Command.Empty>
                <Command.Group
                  heading="Screens"
                  className="px-1 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:font-mono [&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-faint"
                >
                  {NAV_ITEMS.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Command.Item
                        key={item.href}
                        value={`${item.label} ${item.hint}`}
                        onSelect={() => go(item.href)}
                        className="flex cursor-pointer items-center gap-3 rounded-control px-2.5 py-2 text-sm text-muted data-[selected=true]:bg-accent-soft data-[selected=true]:text-ink"
                      >
                        <Icon size={16} className="shrink-0 text-faint" />
                        <span className="text-ink">{item.label}</span>
                        <span className="ml-auto truncate text-[12px] text-faint">
                          {item.hint}
                        </span>
                      </Command.Item>
                    );
                  })}
                </Command.Group>
              </Command.List>
            </Command>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
