import type { Metadata } from "next";
import Link from "next/link";
import { Section, SectionHead } from "@/components/ui/Section";
import { Badge } from "@/components/ui/Badge";
import { pageMetadata } from "@/lib/metadata";
import { downloadUrls, hasRepo, releasesUrl, siteConfig } from "@/content/site";

export const metadata: Metadata = pageMetadata({
  title: "Download",
  description:
    "Download Evano Studio for macOS and Windows — free, open-source, local AI agents in one app.",
  path: "/download",
});

const prerequisites = [
  {
    title: "Your own computer",
    text: "Local AI runs on your hardware. 16 GB of RAM is a comfortable starting point; more lets you run larger, faster models.",
  },
  {
    title: "Ollama (free)",
    text: "The local AI runtime. A normal app install — Evano Studio guides you to it and never installs software silently.",
  },
  {
    title: "A local model (free)",
    text: "Pulled through Ollama with one click from inside the app. We recommend Gemma 4; Qwen, Llama, Mistral, and DeepSeek also work.",
  },
  {
    title: "ComfyUI (optional, free)",
    text: "Only for local image generation. Everything else works without it.",
  },
];

const platforms = [
  {
    icon: "",
    name: "macOS",
    meta: "Apple Silicon (M-series) · macOS 13+ · .dmg",
    url: downloadUrls.mac,
    primary: true,
  },
  {
    icon: "⊞",
    name: "Windows",
    meta: "Windows 10 / 11 · 64-bit · .exe installer",
    url: downloadUrls.windows,
    primary: false,
  },
];

export default function DownloadPage() {
  return (
    <>
      <div className="container page-header">
        <Badge variant="free">100% free — no account needed</Badge>
        <h1 className="page-title">Download Evano Studio</h1>
        <p className="page-lead">
          One app for macOS and Windows. Your AI team runs locally — nothing to
          pay, nothing to sign up for.
        </p>
      </div>

      <Section flush>
        <div className="dl-grid">
          {platforms.map((p) => (
            <article key={p.name} className="dl-card">
              <span className="dl-icon" aria-hidden="true">{p.icon}</span>
              <h3>Evano Studio for {p.name}</h3>
              <span className="dl-meta">{p.meta}</span>
              {hasRepo ? (
                <a
                  className={`btn ${p.primary ? "btn--primary" : "btn--secondary"} btn--lg`}
                  href={p.url}
                  download
                >
                  ⬇ Download for {p.name}
                </a>
              ) : (
                <span className="btn btn--secondary btn--disabled" aria-disabled="true">
                  First alpha build coming soon
                </span>
              )}
            </article>
          ))}
        </div>

        <div className="callout" style={{ maxWidth: 760, marginTop: 24 }}>
          <strong>Alpha honesty:</strong> early builds are unsigned, so your OS
          may ask you to allow the app the first time (right-click → Open on
          macOS, “More info → Run anyway” on Windows). Until the first packaged
          release lands you can{" "}
          <Link href="/docs/getting-started">run it from source</Link> — it takes
          about five minutes.
        </div>

        <div className="cta-actions" style={{ justifyContent: "flex-start", marginTop: 24 }}>
          <a
            className="btn btn--secondary"
            href={siteConfig.links.github}
            aria-disabled={!hasRepo}
            rel="noopener noreferrer"
          >
            ★ Star on GitHub
          </a>
          <a className="btn btn--ghost" href={releasesUrl} rel="noopener noreferrer">
            All versions &amp; release notes
          </a>
          <Link className="btn btn--ghost" href="/docs/getting-started">
            Run from source (free, ~5 min)
          </Link>
        </div>
      </Section>

      <Section alt>
        <SectionHead
          eyebrow="Before you start"
          title="What you'll need locally"
          subtitle="Everything on this list is free. The only thing you bring is your own hardware."
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
