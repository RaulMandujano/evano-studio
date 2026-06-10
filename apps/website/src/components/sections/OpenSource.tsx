import { Section, SectionHead } from "@/components/ui/Section";
import { siteConfig, techStack } from "@/content/site";

export function OpenSource() {
  return (
    <Section id="open-source" alt>
      <SectionHead
        eyebrow="Open source &amp; free"
        title="Built in the open, free by default"
        subtitle="Evano Studio is an open-source project that wraps a professional experience around free, local, open tools. No paid AI API, no Chroma Cloud, no paid vector DB, and no paid image API are required by default."
      />

      <div className="grid grid--2" style={{ alignItems: "start" }}>
        <article className="card">
          <h3 className="card-title">What you need (locally)</h3>
          <ul className="check-list" style={{ marginTop: 12 }}>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>
                <strong>Your own computer</strong> — local AI runs on your
                hardware.
              </span>
            </li>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>
                <strong>Ollama</strong> and at least one local model (Gemma 4
                recommended).
              </span>
            </li>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>
                <strong>ComfyUI</strong> — optional, only for local image
                generation.
              </span>
            </li>
          </ul>
        </article>

        <article className="card">
          <h3 className="card-title">The local stack</h3>
          <ul className="check-list" style={{ marginTop: 12 }}>
            {techStack.map((t) => (
              <li key={t.name} className="check-item">
                <span className="tick">•</span>
                <span>
                  <strong>{t.name}</strong> — {t.role}
                </span>
              </li>
            ))}
          </ul>
        </article>
      </div>

      <div className="cta-actions" style={{ justifyContent: "flex-start", marginTop: 28 }}>
        <a
          className="btn btn--secondary"
          href={siteConfig.links.github}
          aria-disabled={siteConfig.links.github === "#"}
          rel="noopener noreferrer"
        >
          View on GitHub (coming soon)
        </a>
      </div>
    </Section>
  );
}
