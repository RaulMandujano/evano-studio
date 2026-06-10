import Link from "next/link";
import { Section } from "@/components/ui/Section";

export default function NotFound() {
  return (
    <Section flush>
      <div className="center" style={{ paddingBlock: 60 }}>
        <span className="eyebrow">404</span>
        <h1 className="page-title">Page not found</h1>
        <p className="page-lead" style={{ marginInline: "auto" }}>
          The page you&apos;re looking for doesn&apos;t exist or has moved.
        </p>
        <div className="cta-actions" style={{ marginTop: 24 }}>
          <Link className="btn btn--primary" href="/">
            Back to home
          </Link>
        </div>
      </div>
    </Section>
  );
}
