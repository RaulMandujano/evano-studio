import { Section } from "@/components/ui/Section";

export function LocalImageGeneration() {
  return (
    <Section id="image-generation" alt>
      <div className="split split--reverse">
        <div>
          <span className="eyebrow">Local image generation</span>
          <h2 className="split-title">Images, generated locally and optionally</h2>
          <p className="split-text">
            Agents help you craft strong image prompts. When you want to turn
            those prompts into pictures, Evano Studio can connect to your own
            local <strong>ComfyUI</strong> instance — no paid image APIs, no
            cloud services.
          </p>
          <ul className="check-list">
            <li className="check-item">
              <span className="tick">✓</span>
              <span>
                <strong>Optional &amp; local</strong> — ComfyUI is an external
                service you install and run yourself.
              </span>
            </li>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>No paid image API — ever.</span>
            </li>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>Generated images are saved to your local workspace.</span>
            </li>
          </ul>
          <p className="muted" style={{ marginTop: 16, fontSize: "0.92rem" }}>
            Prompt generation works on its own. Image rendering simply stays
            disabled until you configure ComfyUI.
          </p>
        </div>
        <div className="split-media">
          <div className="panel" aria-hidden="true">
            <div className="panel-bar">
              <span />
              <span />
              <span />
            </div>
            <div
              style={{
                aspectRatio: "16 / 10",
                borderRadius: 12,
                border: "1px solid var(--border)",
                background:
                  "linear-gradient(135deg, var(--accent-soft), var(--teal-soft))",
              }}
            />
            <div className="panel-line w-60" style={{ marginTop: 14 }} />
          </div>
        </div>
      </div>
    </Section>
  );
}
