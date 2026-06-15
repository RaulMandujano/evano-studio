import { Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";

/** Dark product mockup: prompt → generated image, saved locally. */
function ImageMockup() {
  return (
    <div className="mockup mockup--sm" aria-hidden="true">
      <div className="mockup-bar">
        <span className="mockup-dot" />
        <span className="mockup-dot" />
        <span className="mockup-dot" />
        <span className="mockup-title">Evano Studio — Images</span>
      </div>
      <div className="mockup-main">
        <div className="mk-row" style={{ marginBottom: 12 }}>
          <span className="mk-ico">✨</span> &ldquo;A cozy coffee shop logo, warm
          sunset palette&rdquo;
        </div>
        <div
          style={{
            aspectRatio: "16 / 10",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.1)",
            background:
              "radial-gradient(120% 120% at 20% 10%, #ff6b35, transparent 55%), radial-gradient(120% 120% at 90% 90%, #ff2d78, transparent 55%), #2a1420",
          }}
        />
        <div className="mk-row" style={{ marginTop: 12 }}>
          <span className="mk-ico">🖼️</span> coffee-logo.png
          <span className="mk-pill mk-pill--ok">saved to workspace</span>
        </div>
      </div>
    </div>
  );
}

export function LocalImageGeneration() {
  return (
    <Section id="image-generation" alt>
      <div className="split split--reverse">
        <Reveal>
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
        </Reveal>
        <Reveal className="split-media reveal-d1" scale>
          <ImageMockup />
        </Reveal>
      </div>
    </Section>
  );
}
