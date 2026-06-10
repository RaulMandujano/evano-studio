import Link from "next/link";
import { Section } from "@/components/ui/Section";

/** Closing call-to-action band used on the home page. */
export function DownloadCta() {
  return (
    <Section id="download-cta">
      <div className="cta-band">
        <h2>Ready when you are</h2>
        <p>
          Evano Studio is in early alpha and not yet available to download. Follow
          the project to know when the first release lands.
        </p>
        <div className="cta-actions">
          <Link className="btn btn--primary" href="/download">
            Download details
          </Link>
          <Link className="btn btn--secondary" href="/roadmap">
            See the roadmap
          </Link>
        </div>
      </div>
    </Section>
  );
}
