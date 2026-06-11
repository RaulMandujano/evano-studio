import Link from "next/link";
import { Section } from "@/components/ui/Section";
import { downloadUrls, hasRepo } from "@/content/site";

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
          <Link className="btn btn--ghost" href="/download">
            All options
          </Link>
        </div>
      </div>
    </Section>
  );
}
