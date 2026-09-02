import type { Metadata } from "next";
import { Onest, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Deliberately off the Inter/Geist default. Onest is a warm, humanist UI
// grotesk — clean but with its own character, so the type doesn't read as
// stock AI output.
const onest = Onest({
  subsets: ["latin"],
  variable: "--font-ui",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono-jb",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Orchestrator — Agent Control Room",
    template: "%s · Orchestrator",
  },
  description:
    "A control room for autonomous multi-agent workflows: plan, delegate, review, escalate, and replay — every decision traced and costed.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      data-theme="light"
      className={`${onest.variable} ${jetbrainsMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="h-full overflow-hidden">{children}</body>
    </html>
  );
}
