import type { Metadata } from "next";
import { Badge } from "@/components/ui/Badge";
import { pageMetadata } from "@/lib/metadata";

export const metadata: Metadata = pageMetadata({
  title: "Privacy",
  description:
    "Evano Studio is privacy-first and local-first. Your data stays on your machine and nothing is uploaded to the cloud by default.",
  path: "/privacy",
});

export default function PrivacyPage() {
  return (
    <>
      <div className="container page-header">
        <Badge variant="free" dot>
          Privacy-first
        </Badge>
        <h1 className="page-title">Privacy</h1>
        <p className="page-lead">
          Evano Studio is local-first and privacy-first by design. This page
          explains, in plain language, how your data is handled.
        </p>
      </div>

      <section className="section section--flush">
        <div className="container">
          <div className="prose">
            <h2>The short version</h2>
            <p>
              Evano Studio runs on your computer. Your models, documents,
              knowledge base, chats, and logs stay on your machine. Nothing is
              uploaded to the cloud by default.
            </p>

            <h2>What stays local</h2>
            <ul>
              <li>
                <strong>AI models and inference</strong> run locally through
                Ollama — there are no remote model calls.
              </li>
              <li>
                <strong>Your documents and knowledge base</strong> are stored
                locally (SQLite for app data, ChromaDB for the knowledge base).
              </li>
              <li>
                <strong>Chats and generated files</strong> are saved to your
                local workspace.
              </li>
              <li>
                <strong>Logs</strong> are kept on your machine to help you
                troubleshoot.
              </li>
            </ul>

            <h2>No cloud upload by default</h2>
            <p>
              Evano Studio does not send your content to any server. There is no
              account to create, no telemetry that profiles you, and no paid API
              calls. If any optional feature ever sends data off your device, it
              will be clearly labeled and turned off by default.
            </p>

            <h2>Support bundles</h2>
            <p>
              When you create a support bundle to report a problem, it excludes
              your private chat and document contents by default. You see what it
              contains before sharing it, and creating it never sends it anywhere
              automatically.
            </p>

            <h2>This website</h2>
            <p>
              This site practices what the product preaches: no tracking and no
              third-party profiling analytics by default.
            </p>

            <h2>Status</h2>
            <p>
              Evano Studio is in early alpha. This page describes the project&apos;s
              privacy principles and will be expanded into a formal privacy
              policy before the first public release.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
