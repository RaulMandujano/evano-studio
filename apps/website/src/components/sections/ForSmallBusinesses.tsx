import { Section, SectionHead } from "@/components/ui/Section";

const useCases = [
  {
    title: "Knowledge assistant",
    text: "Answer staff questions from your own handbooks and documents using local retrieval.",
  },
  {
    title: "Document drafter",
    text: "Generate proposals, summaries, and product descriptions saved straight to your workspace.",
  },
  {
    title: "Marketing helper",
    text: "Turn ideas into social copy and image prompts — and images, if you run ComfyUI.",
  },
  {
    title: "Onboarding buddy",
    text: "Help new hires get answers from an internal knowledge base, on demand.",
  },
];

export function ForSmallBusinesses() {
  return (
    <Section id="for-business" alt>
      <SectionHead
        eyebrow="For small businesses"
        title="Create local AI employees for your business"
        subtitle="Evano Studio is a control center, not a developer tool. Build AI agents that handle repeatable work — privately, on your own hardware."
      />
      <div className="grid grid--2">
        {useCases.map((u) => (
          <article key={u.title} className="card">
            <h3 className="card-title">{u.title}</h3>
            <p className="card-text">{u.text}</p>
          </article>
        ))}
      </div>
      <p className="muted mt-sm" style={{ marginTop: 24 }}>
        Each example is just an agent configuration — a model, a role, and a set
        of permitted tools. Nothing leaves your machine.
      </p>
    </Section>
  );
}
