import type { Metadata } from "next";
import Link from "next/link";
import { Section, SectionHead } from "@/components/ui/Section";
import { Badge } from "@/components/ui/Badge";
import { pageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/content/site";

export const metadata: Metadata = pageMetadata({
  title: "Download",
  description:
    "Evano Studio is in early alpha. There is no public download yet. Here is what you will need and how to follow progress.",
  path: "/download",
});

const prerequisites = [
  {
    title: "Your own computer",
    text: "Local AI runs on your hardware. More RAM and a better GPU/CPU let you run larger, faster models.",
  },
  {
    title: "Ollama",
    text: "The free local AI runtime. You install it yourself — Evano Studio never installs software silently.",
  },
  {
    title: "A local model",
    text: "Pull at least one model through Ollama. We recommend Gemma 4 when available; Qwen, Llama, Mistral, and DeepSeek also work.",
  },
  {
    title: "ComfyUI (optional)",
    text: "Only needed for local image generation. Everything else works without it.",
  },
];

export default function DownloadPage() {
  return (
    <>
      <div className="container page-header">
        <Badge variant="alpha" dot>
          Alpha — no public download yet
        </Badge>
        <h1 className="page-title">Download Evano Studio</h1>
        <p className="page-lead">
          Evano Studio is still in active development. We are not distributing a
          build yet, and we will not post a download link until there is a real,
          installable release.
        </p>
      </div>

      <Section flush>
        <div className="callout" style={{ maxWidth: 760 }}>
          <strong>No download available yet.</strong> macOS will be the first
          supported platform. This page will be updated with verified
          instructions when the first alpha is ready — see the{" "}
          <Link href="/roadmap">roadmap</Link>.
        </div>

        <div className="grid grid--3" style={{ marginTop: 24 }}>
          <article className="card">
            <h3 className="card-title">macOS</h3>
            <p className="card-text">First supported platform.</p>
            <span className="btn btn--primary btn--disabled" aria-disabled="true">
              Coming soon
            </span>
          </article>
          <article className="card">
            <h3 className="card-title">Windows</h3>
            <p className="card-text">Planned after macOS.</p>
            <span className="btn btn--secondary btn--disabled" aria-disabled="true">
              Later
            </span>
          </article>
          <article className="card">
            <h3 className="card-title">Linux</h3>
            <p className="card-text">Planned after Windows.</p>
            <span className="btn btn--secondary btn--disabled" aria-disabled="true">
              Later
            </span>
          </article>
        </div>

        <div className="cta-actions" style={{ justifyContent: "flex-start", marginTop: 24 }}>
          <a
            className="btn btn--secondary"
            href={siteConfig.links.github}
            aria-disabled={siteConfig.links.github === "#"}
            rel="noopener noreferrer"
          >
            View on GitHub
          </a>
          <Link className="btn btn--ghost" href="/docs/getting-started">
            Read Getting started
          </Link>
        </div>
      </Section>

      <Section alt>
        <SectionHead
          eyebrow="Before you start"
          title="What you'll need locally"
          subtitle="Everything here is free. The only real cost is your own hardware."
        />
        <div className="grid grid--2">
          {prerequisites.map((p) => (
            <article key={p.title} className="card">
              <h3 className="card-title">{p.title}</h3>
              <p className="card-text">{p.text}</p>
            </article>
          ))}
        </div>
      </Section>
    </>
  );
}
