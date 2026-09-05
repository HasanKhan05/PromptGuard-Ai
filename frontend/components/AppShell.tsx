"use client";

import type { ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FlaskConical, LayoutDashboard, MessageSquareText, Microscope } from "lucide-react";

const nav = [
  { href: "/", label: "Assistant", icon: MessageSquareText },
  { href: "/experiments", label: "Experiments", icon: FlaskConical },
  { href: "/benchmarks", label: "Benchmarks", icon: LayoutDashboard },
  { href: "/research", label: "Research", icon: Microscope },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand">
            <Image src="/promptguard-logo.png" alt="PromptGuard Ai" width={36} height={36} priority />
            <div>
              <div className="brand-title">PromptGuard Ai</div>
              <div className="brand-subtitle">Developer assistant + research lab</div>
            </div>
          </div>

          <nav className="nav-list" aria-label="Main navigation">
            {nav.map(({ href, label, icon: Icon }) => {
              const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
              return (
                <Link key={href} href={href} className={`nav-item ${active ? "active" : ""}`}>
                  <Icon size={15} strokeWidth={1.8} />
                  <span>{label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="research-owner-card">
          <div className="eyebrow">Research &amp; Development</div>
          <strong>Muhammad Hasan Dad Khan</strong>
        </div>
      </aside>

      <main className="main-area">{children}</main>
    </div>
  );
}
