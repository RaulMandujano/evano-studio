import { Section } from "@/components/ui/Section";

export function LocalDocumentsRAG() {
  return (
    <Section id="knowledge-base">
      <div className="split">
        <div>
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
        </div>
        <div className="split-media">
          <div className="panel" aria-hidden="true">
            <div className="panel-bar">
              <span />
              <span />
              <span />
            </div>
            <div className="panel-line w-90 accent" />
            <div className="panel-line w-80" />
            <div className="panel-line w-60" />
            <div className="panel-line w-90" />
            <div className="panel-line w-80" />
          </div>
        </div>
      </div>
    </Section>
  );
}
