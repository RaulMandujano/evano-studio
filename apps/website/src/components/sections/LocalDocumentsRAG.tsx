import { Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";

/** Dark product mockup: a knowledge base + an agent answer grounded in sources. */
function RagMockup() {
  return (
    <div className="mockup mockup--sm" aria-hidden="true">
      <div className="mockup-bar">
        <span className="mockup-dot" />
        <span className="mockup-dot" />
        <span className="mockup-dot" />
        <span className="mockup-title">Evano Studio — Knowledge Base</span>
      </div>
      <div className="mockup-main">
        <div className="mk-rows" style={{ marginBottom: 14 }}>
          <div className="mk-row">
            <span className="mk-ico">📄</span> Employee-Handbook.pdf
            <span className="mk-pill mk-pill--ok">indexed</span>
          </div>
          <div className="mk-row">
            <span className="mk-ico">📄</span> Refund-Policy.md
            <span className="mk-pill mk-pill--ok">indexed</span>
          </div>
        </div>
        <div className="mk-chat">
          <div className="mk-msg mk-msg--user">What&apos;s our refund window?</div>
          <div className="mk-msg mk-msg--bot">
            Customers can request a refund within 30 days of purchase.
            <span className="mk-src">Sources: Refund-Policy.md</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function LocalDocumentsRAG() {
  return (
    <Section id="knowledge-base">
      <div className="split">
        <Reveal>
          <span className="eyebrow">Local documents &amp; RAG</span>
          <h2 className="split-title">Your knowledge base, on your machine</h2>
          <p className="split-text">
            Import your own documents into a local knowledge base powered by{" "}
            <strong>ChromaDB</strong>. Evano Studio chunks and embeds them
            locally, so your agents can answer questions grounded in your
            content — using retrieval-augmented generation.
          </p>
          <ul className="check-list">
            <li className="check-item">
              <span className="tick">✓</span>
              <span>
                <strong>ChromaDB local only</strong> — no Chroma Cloud, no paid
                vector database.
              </span>
            </li>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>Local embeddings — your documents never leave the device.</span>
            </li>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>Agents search only the knowledge bases you allow.</span>
            </li>
          </ul>
        </Reveal>
        <Reveal className="split-media reveal-d1" scale>
          <RagMockup />
        </Reveal>
      </div>
    </Section>
  );
}
