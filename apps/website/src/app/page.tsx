import Link from "next/link";
import { Hero } from "@/components/sections/Hero";
import { FreeByDefault } from "@/components/sections/FreeByDefault";
import { Features } from "@/components/sections/Features";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { ForSmallBusinesses } from "@/components/sections/ForSmallBusinesses";
import { LocalDocumentsRAG } from "@/components/sections/LocalDocumentsRAG";
import { LocalImageGeneration } from "@/components/sections/LocalImageGeneration";
import { VisualRoutinesCalendar } from "@/components/sections/VisualRoutinesCalendar";
import { OpenSource } from "@/components/sections/OpenSource";
import { DownloadCta } from "@/components/sections/DownloadCta";
import { FaqList } from "@/components/sections/FaqList";
import { Section, SectionHead } from "@/components/ui/Section";

export default function HomePage() {
  return (
    <>
      <Hero />
      <FreeByDefault />
      <Features />
      <HowItWorks />
      <ForSmallBusinesses />
      <LocalDocumentsRAG />
      <LocalImageGeneration />
      <VisualRoutinesCalendar />
      <OpenSource />

      <Section id="faq">
        <SectionHead
          eyebrow="FAQ"
          title="Common questions"
          subtitle="A few of the things people ask most."
        />
        <FaqList limit={4} />
        <p className="mt-sm" style={{ marginTop: 20 }}>
          <Link href="/faq">See all questions →</Link>
        </p>
      </Section>

      <DownloadCta />
    </>
  );
}
