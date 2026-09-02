"use client";

import { useEffect, useState } from "react";

function format(d: Date) {
  const day = d.toLocaleDateString([], { weekday: "short" });
  const date = d.toLocaleDateString([], { month: "short", day: "numeric" });
  const time = d.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${day} ${date}  ${time}`;
}

export function Clock() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 15_000);
    return () => clearInterval(id);
  }, []);

  // Render nothing until mounted to avoid a hydration mismatch.
  return (
    <span className="tabular-nums text-white/90">
      {now ? format(now) : ""}
    </span>
  );
}
