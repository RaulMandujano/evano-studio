import type { Metadata } from "next";
import { siteConfig } from "@/content/site";

/**
 * Build SEO-friendly per-page metadata with sensible Open Graph / Twitter
 * defaults. Pass a path so canonical/OG URLs are correct.
 */
export function pageMetadata(options: {
  title: string;
  description: string;
  path?: string;
}): Metadata {
  const { title, description, path = "/" } = options;
  const url = new URL(path, siteConfig.url).toString();

  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      type: "website",
      siteName: siteConfig.name,
      title: `${title} — ${siteConfig.name}`,
      description,
      url,
    },
    twitter: {
      card: "summary_large_image",
      title: `${title} — ${siteConfig.name}`,
      description,
    },
  };
}
