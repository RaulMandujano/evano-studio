import { Section, SectionHead } from "@/components/ui/Section";
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
        {features.map((f) => (
          <article key={f.title} className="card card--feature">
            <span className="card-icon" aria-hidden="true">
              {f.icon}
            </span>
            <h3 className="card-title">{f.title}</h3>
            <p className="card-text">{f.description}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
