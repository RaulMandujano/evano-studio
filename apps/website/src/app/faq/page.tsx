import type { Metadata } from "next";
import { FaqList } from "@/components/sections/FaqList";
import { Section } from "@/components/ui/Section";
import { Badge } from "@/components/ui/Badge";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata({
  title: "FAQ",
  description:
    "Answers to common questions about Evano Studio — cost, privacy, hardware, supported models, image generation, and project status.",
  path: "/faq",
});

export default function FaqPage() {
  return (
    <>
      <div className="container page-header">
        <Badge variant="alpha" dot>
          Alpha
        </Badge>
        <h1 className="page-title">Frequently asked questions</h1>
        <p className="page-lead">
          Honest answers about what Evano Studio is, what it costs (nothing), and
          where the project stands today.
        </p>
      </div>

      <Section flush>
        <FaqList />
      </Section>
    </>
  );
}
