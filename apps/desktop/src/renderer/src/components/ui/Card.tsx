import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

/** Basic surface container. */
export function Card({ children, className }: CardProps) {
  return <div className={`card${className ? ` ${className}` : ""}`}>{children}</div>;
}
