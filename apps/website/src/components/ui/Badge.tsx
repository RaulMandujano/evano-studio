import type { ReactNode } from "react";

type BadgeProps = {
  variant?: "default" | "alpha" | "free";
  dot?: boolean;
  children: ReactNode;
};

/** Small status / label pill. */
export function Badge({ variant = "default", dot, children }: BadgeProps) {
  const cls = ["badge"];
  if (variant === "alpha") cls.push("badge--alpha");
  if (variant === "free") cls.push("badge--free");

  return (
    <span className={cls.join(" ")}>
      {dot ? <span className="dot" aria-hidden="true" /> : null}
      {children}
    </span>
  );
}
