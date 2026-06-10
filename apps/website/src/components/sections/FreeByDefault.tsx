import { Section, SectionHead } from "@/components/ui/Section";

const points = [
  { big: "$0", text: "No API keys, no subscriptions, no metered usage. Ever." },
  { big: "100% local", text: "Models, chats, documents, and images live on your machine." },
  { big: "Open source", text: "AGPL-3.0 licensed — read it, fork it, improve it." },
  { big: "Mac + Windows", text: "One app, both platforms, the same free experience." },
];

/** The "what does free actually mean" band — the core promise, spelled out. */
export function FreeByDefault() {
  return (
    <Section alt id="free">
      <SectionHead
        eyebrow="Free by default"
        title="Free actually means free"
        subtitle="Evano Studio runs on free local models through Ollama. Your hardware is the only thing you bring."
      />
      <div className="free-band">
        {points.map((p) => (
          <article key={p.big} className="free-item">
            <span className="free-big">{p.big}</span>
            <p>{p.text}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
