import type { ReactNode } from "react";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PromptGuard Ai — Cross-Model Prompt-Injection Research",
  description: "A frozen paired benchmark of prompt-injection robustness, mapped guardrails, and legitimate-task utility across four model configurations.",
  metadataBase: new URL("https://hasankhan05.github.io/PromptGuard-Ai/"),
  openGraph: {
    title: "PromptGuard Ai — Cross-Model Prompt-Injection Research",
    description: "Final frozen results from a paired prompt-injection and guardrail benchmark.",
    type: "website",
  },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
