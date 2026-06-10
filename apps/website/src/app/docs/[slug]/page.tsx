import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Section } from "@/components/ui/Section";
import { Badge } from "@/components/ui/Badge";
import { DocBody } from "@/components/docs/DocBody";
import { pageMetadata } from "@/lib/metadata";
import { docArticles, getDoc } from "@/content/docs";

export function generateStaticParams() {
  return docArticles.map((doc) => ({ slug: doc.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const doc = getDoc(slug);
  if (!doc) return pageMetadata({ title: "Docs", description: "Documentation", path: "/docs" });
  return pageMetadata({ title: doc.title, description: doc.description, path: `/docs/${slug}` });
}

export default async function DocArticlePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const doc = getDoc(slug);
  if (!doc) notFound();

  return (
    <>
      <div className="container page-header">
        <Badge variant="alpha" dot>
          Alpha
        </Badge>
        <p className="doc-breadcrumb">
          <Link href="/docs">Docs</Link> / {doc.title}
        </p>
        <h1 className="page-title">{doc.title}</h1>
        <p className="page-lead">{doc.description}</p>
      </div>

      <Section flush>
        <DocBody blocks={doc.blocks} />
        <p className="mt-sm" style={{ marginTop: 28 }}>
          <Link href="/docs">← Back to all docs</Link>
        </p>
      </Section>
    </>
  );
}
