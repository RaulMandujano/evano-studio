import type { ReactNode } from "react";

export type BadgeTone = "neutral" | "ok" | "pending" | "info" | "alpha" | "danger";

interface BadgeProps {
  tone?: BadgeTone;
  dot?: boolean;
  children: ReactNode;
}

export function Badge({ tone = "neutral", dot, children }: BadgeProps) {
  return (
    <span className={`badge badge--${tone}`}>
      {dot ? <span className="badge-dot" aria-hidden="true" /> : null}
      {children}
    </span>
  );
}
