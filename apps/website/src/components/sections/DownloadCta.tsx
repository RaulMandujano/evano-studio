import Link from "next/link";
import { Section } from "@/components/ui/Section";

/** Closing call-to-action band used on the home page. */
export function DownloadCta() {
  return (
    <Section id="download-cta">
      <div className="cta-band">
        <h2>Hire your first AI employee today</h2>
        <p>
          Free forever, running on your own Mac or Windows PC. Set up in minutes —
          the app guides you through everything.
        </p>
        <div className="cta-actions">
          <Link className="btn btn--primary btn--lg" href="/download">
             Download for macOS
          </Link>
          <Link className="btn btn--secondary btn--lg" href="/download">
            ⊞ Download for Windows
          </Link>
        </div>
      </div>
    </Section>
  );
}
