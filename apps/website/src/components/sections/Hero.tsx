import Link from "next/link";
import { Badge } from "@/components/ui/Badge";

export function Hero() {
  return (
    <section className="hero">
      <div className="container hero-inner">
        <div className="hero-badges">
          <Badge variant="alpha" dot>
            Alpha — in active development
          </Badge>
          <Badge variant="free">Free by default</Badge>
        </div>

        <h1 className="hero-title">
          Local AI agents <span className="grad">without the terminal</span>
        </h1>

        <p className="hero-subtitle">
          Evano Studio is a free, open-source desktop app for creating and
          managing local AI agents for your business — without paid APIs, cloud
          lock-in, or a single command line.
        </p>

        <div className="hero-actions">
          <Link className="btn btn--primary" href="/download">
            Get Evano Studio
          </Link>
          <Link className="btn btn--secondary" href="/docs">
            Read the docs
          </Link>
        </div>

        <ul className="hero-points">
          <li>
            <span className="tick">✓</span> Runs on your machine
          </li>
          <li>
            <span className="tick">✓</span> Powered by Ollama
          </li>
          <li>
            <span className="tick">✓</span> No cloud required
          </li>
          <li>
            <span className="tick">✓</span> Open source
          </li>
        </ul>
      </div>
    </section>
  );
}
