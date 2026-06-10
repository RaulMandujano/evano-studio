import type { Metadata } from "next";
import Link from "next/link";
import { Section } from "@/components/ui/Section";
import { Badge } from "@/components/ui/Badge";
import { pageMetadata } from "@/lib/metadata";
import { docGroups, getDoc } from "@/content/docs";

export const metadata: Metadata = pageMetadata({
  title: "Documentation",
  description:
    "Guides for Evano Studio — getting started, installing Ollama and local models, agents, knowledge base (RAG), ComfyUI image generation, routines, privacy, and more.",
  path: "/docs",
});

export default function DocsPage() {
  return (
    <>
      <div className="container page-header">
        <Badge variant="alpha" dot>
          Alpha
        </Badge>
        <h1 className="page-title">Documentation</h1>
        <p className="page-lead">
          Everything is local and free by default. Some local tools (Ollama, and
          optionally ComfyUI) need a one-time local installation — these guides walk
          you through it honestly.
        </p>
      </div>

      <Section flush>
        {docGroups.map((group) => (
          <div key={group.title} className="docs-group">
            <h2 className="section-title docs-group-title">{group.title}</h2>
            <div className="grid grid--3">
              {group.slugs.map((slug) => {
                const doc = getDoc(slug);
                if (!doc) return null;
                return (
                  <Link key={slug} href={`/docs/${slug}`} className="card doc-card">
                    <h3 className="card-title">{doc.title}</h3>
                    <p className="card-text">{doc.description}</p>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}

        <p className="mt-sm" style={{ marginTop: 28 }}>
          Looking for the bigger picture? See the <Link href="/roadmap">roadmap</Link>{" "}
          or the <Link href="/faq">FAQ</Link>.
        </p>
      </Section>
    </>
  );
}
