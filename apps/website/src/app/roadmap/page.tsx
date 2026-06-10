import type { Metadata } from "next";
import { Section } from "@/components/ui/Section";
import { Badge } from "@/components/ui/Badge";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata({
  title: "Roadmap",
  description:
    "The Evano Studio development roadmap — what is done, what is in progress, and what is planned before the first public alpha.",
  path: "/roadmap",
});

type Status = "done" | "current" | "planned";

const phases: { tag: string; status: Status; title: string; text: string }[] = [
  {
    tag: "Done",
    status: "done",
    title: "Foundation & desktop shell",
    text: "Docs, monorepo, the website, and a secure Electron + React desktop shell.",
  },
  {
    tag: "Done",
    status: "done",
    title: "Local backend & Ollama",
    text: "FastAPI backend, SQLite data layer, Ollama integration, model detection, and model installs.",
  },
  {
    tag: "Done",
    status: "done",
    title: "Agents, chat & documents",
    text: "Create/manage agents, chat with local models, and create local documents with safe tools.",
  },
  {
    tag: "Done",
    status: "done",
    title: "Knowledge base (RAG)",
    text: "Import .txt/.md into a local ChromaDB knowledge base with local embeddings; agents answer from it.",
  },
  {
    tag: "Done",
    status: "done",
    title: "Routines, calendar & images",
    text: "Schedule agent tasks on a visual calendar, and optional local image generation via ComfyUI.",
  },
  {
    tag: "Done",
    status: "done",
    title: "Logging & support bundle",
    text: "Structured local logs and a privacy-respecting support bundle for troubleshooting.",
  },
  {
    tag: "Now",
    status: "current",
    title: "Packaging for public alpha",
    text: "macOS packaging, app icons, bundling the local backend, and an honest download.",
  },
  {
    tag: "Next",
    status: "planned",
    title: "Signing, Windows & polish",
    text: "Code signing/notarization, a Windows build, and refinements ahead of a wider release.",
  },
];

const statusLabel: Record<Status, string> = {
  done: "Done",
  current: "In progress",
  planned: "Planned",
};

export default function RoadmapPage() {
  return (
    <>
      <div className="container page-header">
        <Badge variant="alpha" dot>
          Alpha
        </Badge>
        <h1 className="page-title">Roadmap</h1>
        <p className="page-lead">
          Evano Studio is built step by step, in the open. This roadmap is a
          living plan and the order may shift as the project evolves.
        </p>
      </div>

      <Section flush>
        <div className="phase-list">
          {phases.map((p, i) => (
            <div key={`${p.tag}-${i}`} className="phase">
              <span
                className={
                  "phase-tag" +
                  (p.status === "done"
                    ? " phase-tag--done"
                    : p.status === "current"
                      ? " phase-tag--current"
                      : "")
                }
              >
                {p.tag} · {statusLabel[p.status]}
              </span>
              <div>
                <h3>{p.title}</h3>
                <p>{p.text}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="callout" style={{ maxWidth: 760, marginTop: 28 }}>
          <strong>Not production-ready.</strong> Until the public alpha ships,
          treat everything here as planned work in progress.
        </div>
      </Section>
    </>
  );
}
