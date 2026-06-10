import Link from "next/link";
import { siteConfig } from "@/content/site";

const productLinks = [
  { href: "/", label: "Home" },
  { href: "/download", label: "Download" },
  { href: "/roadmap", label: "Roadmap" },
];

const resourceLinks = [
  { href: "/docs", label: "Documentation" },
  { href: "/faq", label: "FAQ" },
  { href: "/privacy", label: "Privacy" },
];

export function Footer() {
  const year = 2026;

  return (
    <footer className="site-footer">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <Link href="/" className="nav-brand">
              <span className="nav-logo" aria-hidden="true">
                E
              </span>
              {siteConfig.name}
            </Link>
            <p>
              {siteConfig.tagline}. Free by default, local-first, privacy-first,
              and open source.
            </p>
          </div>

          <div className="footer-col">
            <h4>Product</h4>
            {productLinks.map((l) => (
              <Link key={l.href} href={l.href}>
                {l.label}
              </Link>
            ))}
          </div>

          <div className="footer-col">
            <h4>Resources</h4>
            {resourceLinks.map((l) => (
              <Link key={l.href} href={l.href}>
                {l.label}
              </Link>
            ))}
          </div>

          <div className="footer-col">
            <h4>Project</h4>
            <a
              href={siteConfig.links.github}
              aria-disabled={siteConfig.links.github === "#"}
              rel="noopener noreferrer"
            >
              GitHub (coming soon)
            </a>
            <span className="muted" style={{ fontSize: "0.95rem", padding: "4px 0", display: "block" }}>
              Open source
            </span>
          </div>
        </div>

        <div className="footer-bottom">
          <span>
            © {year} {siteConfig.name}. Released under the MIT license.
          </span>
          <span>Status: {siteConfig.status} — not production-ready.</span>
        </div>
      </div>
    </footer>
  );
}
