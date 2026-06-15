import { Section, SectionHead } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { features } from "@/content/site";

export function Features() {
  return (
    <Section id="features" alt>
      <SectionHead
        eyebrow="What you can do"
        title="Everything you need to run local AI agents"
        subtitle="A simple desktop control center for building AI agents that work for your business — all running locally."
      />
      <div className="grid grid--3">
        {features.map((f, i) => (
          <Reveal
            key={f.title}
            as="article"
            className={`card card--feature reveal-d${(i % 3) + 1}`}
          >
            <span className="card-icon" aria-hidden="true">
              {f.icon}
            </span>
            <h3 className="card-title">{f.title}</h3>
            <p className="card-text">{f.description}</p>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
