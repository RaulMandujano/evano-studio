import Link from "next/link";
import { navLinks, siteConfig } from "@/content/site";

/** Sticky top navigation. CSS-only responsive behavior (no client JS). */
export function Header() {
  return (
    <header className="site-header">
      <div className="container">
        <nav className="nav" aria-label="Primary">
          <Link href="/" className="nav-brand">
            <span className="nav-logo" aria-hidden="true">
              E
            </span>
            {siteConfig.name}
          </Link>

          <ul className="nav-links">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="nav-link">
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>

          <div className="nav-actions">
            <a
              className="btn btn--ghost"
              href={siteConfig.links.github}
              aria-disabled={siteConfig.links.github === "#"}
              rel="noopener noreferrer"
            >
              GitHub
            </a>
            <Link className="btn btn--primary" href="/download">
              Download
            </Link>
          </div>
        </nav>
      </div>
    </header>
  );
}
