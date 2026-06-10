import type { MetadataRoute } from "next";
import { siteConfig } from "@/content/site";
import { docArticles } from "@/content/docs";

const routes = ["/", "/docs", "/download", "/roadmap", "/faq", "/privacy"];

export default function sitemap(): MetadataRoute.Sitemap {
  const base: MetadataRoute.Sitemap = routes.map((route) => ({
    url: new URL(route, siteConfig.url).toString(),
    changeFrequency: "weekly",
    priority: route === "/" ? 1 : 0.7,
  }));
  const docs: MetadataRoute.Sitemap = docArticles.map((doc) => ({
    url: new URL(`/docs/${doc.slug}`, siteConfig.url).toString(),
    changeFrequency: "weekly",
    priority: 0.6,
  }));
  return [...base, ...docs];
}
