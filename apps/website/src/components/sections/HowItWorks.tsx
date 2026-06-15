import { Section, SectionHead } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";

const steps = [
  {
    title: "Install Ollama",
    text: "Install the free Ollama runtime and pull a local model. We recommend Gemma 4 when available; Qwen, Llama, Mistral, and DeepSeek also work.",
  },
  {
    title: "Open Evano Studio",
    text: "Launch the desktop app. It detects Ollama and your installed models — no terminal, no config files.",
  },
  {
    title: "Create an agent",
    text: "Give your agent a role, choose a model, and turn on only the tools and permissions it needs.",
  },
  {
    title: "Put it to work",
    text: "Chat, draft documents, search your knowledge base, generate images, or schedule routines on a calendar.",
  },
];

export function HowItWorks() {
  return (
    <Section id="how-it-works">
      <SectionHead
        eyebrow="How it works"
        title="From zero to your first local agent"
        subtitle="No cloud accounts, no API keys. Everything runs on your computer."
      />
      <ol className="steps">
        {steps.map((s, i) => (
          <Reveal key={s.title} as="li" className={`step reveal-d${(i % 4) + 1}`}>
            <span className="step-num">{i + 1}</span>
            <h3>{s.title}</h3>
            <p>{s.text}</p>
          </Reveal>
        ))}
      </ol>
    </Section>
  );
}
