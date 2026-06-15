"use client";

import { useEffect, useRef, useState, type ElementType, type ReactNode } from "react";

type RevealProps = {
  children: ReactNode;
  /** Extra classes (e.g. delay helpers: "reveal-d1") merged with the base reveal. */
  className?: string;
  /** Add a subtle scale-in on top of the upward slide. */
  scale?: boolean;
  /** Render as a different element (default div). */
  as?: ElementType;
};

/**
 * Apple-style scroll reveal: content starts slightly down + transparent, then
 * eases in the first time it scrolls into view. Dependency-free (Intersection-
 * Observer), respects prefers-reduced-motion (handled in CSS), and degrades to
 * fully-visible if JS/observer is unavailable.
 */
export function Reveal({ children, className = "", scale = false, as }: RevealProps) {
  const Tag = (as ?? "div") as ElementType;
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.disconnect();
          }
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      ref={ref}
      className={`reveal${scale ? " reveal--scale" : ""}${visible ? " is-visible" : ""}${
        className ? ` ${className}` : ""
      }`}
    >
      {children}
    </Tag>
  );
}
