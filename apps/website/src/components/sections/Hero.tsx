import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { downloadUrls, hasRepo } from "@/content/site";

/** A tiny CSS-only recreation of the app's Office view — agents at work. */
function AppMockup() {
  return (
    <div className="mockup" aria-hidden="true">
      <div className="mockup-bar">
        <span className="mockup-dot" />
        <span className="mockup-dot" />
        <span className="mockup-dot" />
        <span className="mockup-title">Evano Studio — Office</span>
      </div>
      <div className="mockup-body">
        <div className="mockup-side">
          <span className="mockup-nav is-active">🏢 Office</span>
          <span className="mockup-nav">🤖 Agents</span>
          <span className="mockup-nav">🤝 Teams</span>
          <span className="mockup-nav">🏛️ Org Chart</span>
          <span className="mockup-nav">💬 Chats</span>
        </div>
        <div className="mockup-main">
          <div className="mockup-desks">
            {[
              { emoji: "💼", name: "Daniel", task: "Writing the Q2 report…", busy: true },
              { emoji: "🔎", name: "Leonard", task: "Researching prices…", busy: true },
              { emoji: "💬", name: "Chris", task: "", busy: false },
            ].map((a) => (
              <div key={a.name} className={`mockup-desk ${a.busy ? "is-busy" : ""}`}>
                {a.busy ? <span className="mockup-bubble">{a.task}</span> : null}
                <span className="mockup-screen">
                  {a.busy ? (
                    <span className="mockup-typing">
                      <i />
                      <i />
                      <i />
                    </span>
                  ) : null}
                </span>
                <span className="mockup-worker">{a.busy ? a.emoji : "🪑"}</span>
                <span className="mockup-name">
                  <span className={`mockup-status ${a.busy ? "on" : ""}`} />
                  {a.name}
                </span>
              </div>
            ))}
          </div>
          <div className="mockup-feed">
            <span className="mockup-feed-row">✅ Daniel · Team “Marketing” — step 1/3</span>
            <span className="mockup-feed-row">⏳ Leonard · Routine “Daily prices”</span>
            <span className="mockup-feed-row">💬 Chris · Answered on Discord</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Hero() {
  return (
    <section className="hero">
      <div className="container hero-inner">
        <div className="hero-badges">
          <Badge variant="free">100% free — no API keys, no subscriptions</Badge>
          <Badge variant="alpha" dot>
            Alpha — in active development
          </Badge>
        </div>

        <h1 className="hero-title">
          Your own <span className="grad">AI team</span>, working for you.
          <br />
          Free. Local. One app.
        </h1>

        <p className="hero-subtitle">
          Create AI agents that chat, form teams, follow an org chart, and report
          to you on Discord — all running on <strong>your</strong> computer with
          free local models. No API keys. No subscriptions. No cloud.
        </p>

        <div className="hero-actions">
          {hasRepo ? (
            <>
              <a className="btn btn--primary btn--lg" href={downloadUrls.mac} download>
                 Download for macOS
              </a>
              <a className="btn btn--secondary btn--lg" href={downloadUrls.windows} download>
                ⊞ Download for Windows
              </a>
            </>
          ) : (
            <Link className="btn btn--primary btn--lg" href="/download">
              ⬇ Download
            </Link>
          )}
        </div>

        <p className="hero-platforms">
          macOS (Apple Silicon) · Windows 10/11 · Open source (AGPL-3.0) ·{" "}
          <Link href="/download">all download options</Link>
        </p>

        <AppMockup />

        <ul className="hero-points">
          <li>
            <span className="tick">✓</span> $0 — powered by free local models
          </li>
          <li>
            <span className="tick">✓</span> Your data never leaves your machine
          </li>
          <li>
            <span className="tick">✓</span> No terminal, ever
          </li>
          <li>
            <span className="tick">✓</span> Open source
          </li>
        </ul>
      </div>
    </section>
  );
}
