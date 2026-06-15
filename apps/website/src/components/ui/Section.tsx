import type { ReactNode } from "react";
import { Reveal } from "@/components/ui/Reveal";

type SectionProps = {
  id?: string;
  alt?: boolean;
  flush?: boolean;
  children: ReactNode;
};

/** A page section with a centered container and consistent vertical rhythm. */
export function Section({ id, alt, flush, children }: SectionProps) {
  const classes = ["section"];
  if (alt) classes.push("section--alt");
  if (flush) classes.push("section--flush");

  return (
    <section id={id} className={classes.join(" ")}>
      <div className="container">{children}</div>
    </section>
  );
}

type SectionHeadProps = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  center?: boolean;
};

/** Standard heading block used at the top of most sections. */
export function SectionHead({ eyebrow, title, subtitle, center }: SectionHeadProps) {
  return (
    <Reveal className={`section-head${center ? " section-head--center" : ""}`}>
      {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
      <h2 className="section-title">{title}</h2>
      {subtitle ? <p className="section-subtitle">{subtitle}</p> : null}
    </Reveal>
  );
}
