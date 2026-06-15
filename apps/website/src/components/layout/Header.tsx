import Link from "next/link";
import { hasRepo, navLinks, siteConfig } from "@/content/site";

/** Sticky top navigation. CSS-only responsive behavior (no client JS). */
export function Header() {
  return (
    <header className="site-header">
      <div className="container">
        <nav className="nav" aria-label="Primary">
          <Link href="/" className="nav-brand" aria-label={siteConfig.name}>
            <img
              className="nav-logo"
              src="/evano-mark.svg"
              alt=""
              width={34}
              height={34}
            />
            <span className="nav-wordmark" aria-hidden="true">
              Evano <span className="grad">Studio</span>
            </span>
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
              aria-disabled={!hasRepo}
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
