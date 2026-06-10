/**
 * Documents — everything your agents (and you) have written.
 *
 * Two sources:
 *  1. Agent documents — the work files each OpenClaw agent created in its own
 *     workspace (reports, drafts, team working files), grouped by agent.
 *  2. My documents — files saved through Evano itself (chat exports, routine
 *     outputs from the built-in engine), stored in the Evano workspace.
 */
import { useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { formatBytes } from "../lib/format";
import { timeAgo } from "../lib/office";
import type {
  AgentDocumentsResponse,
  AgentWorkFile,
  DocumentDetail,
  DocumentInfo,
} from "../lib/api/types";

interface PreviewState {
  title: string;
  content: string;
  truncated?: boolean;
}

export function DocumentsView() {
  const agentDocsRes = useBackendResource<AgentDocumentsResponse>(backendApi.getAgentDocuments, "agent-docs");
  const docsRes = useBackendResource<DocumentInfo[]>(backendApi.getDocuments, "evano-docs");
  const documents = docsRes.data ?? [];

  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewState | null>(null);

  const refreshAll = () => {
    agentDocsRes.refresh();
    docsRes.refresh();
  };

  const openPath = async (absPath: string) => {
    setError(null);
    const reveal = window.evano?.documents?.revealPath;
    if (!reveal) {
      setError("Opening the file location isn't available in this environment.");
      return;
    }
    const result = await reveal(absPath);
    if (!result.ok) setError(result.error ?? "Couldn't open the file location.");
  };

  // ---- agent documents -------------------------------------------------- //

  const previewAgentFile = async (agentId: string, file: AgentWorkFile) => {
    setError(null);
    try {
      const r = await backendApi.getAgentDocumentContent(agentId, file.path);
      if (r.ok) setPreview({ title: r.name, content: r.content, truncated: r.truncated });
      else setError(r.message || "Couldn't read the file.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't read the file.");
    }
  };

  const removeAgentFile = async (agentId: string, file: AgentWorkFile) => {
    if (!window.confirm(`Delete "${file.name}" from this agent's folder?`)) return;
    setError(null);
    try {
      const r = await backendApi.deleteAgentDocument(agentId, file.path);
      if (!r.ok) setError(r.message || "Couldn't delete the file.");
      else {
        if (preview?.title === file.name) setPreview(null);
        agentDocsRes.refresh();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't delete the file.");
    }
  };

  const renderAgentDocs = () => {
    if (agentDocsRes.state === "checking") return <p className="muted">Looking into agent folders…</p>;
    if (agentDocsRes.state !== "ready" || !agentDocsRes.data?.ok) {
      return (
        <p className="muted">
          {agentDocsRes.data?.message || "OpenClaw isn't ready — agent documents will show up once it is."}
        </p>
      );
    }
    const groups = agentDocsRes.data.agents.filter((g) => g.files.length > 0);
    if (groups.length === 0) {
      return (
        <p className="muted">
          Nothing yet — when an agent writes a file (a report, a team working file), it appears here.
        </p>
      );
    }
    return groups.map((g) => (
      <div key={g.agent_id} className="doc-agent-group">
        <p className="chat-group-name">
          <span aria-hidden="true">{g.emoji || "🤖"}</span> {g.name}
        </p>
        <ul className="doc-list">
          {g.files.map((f) => (
            <li key={f.path} className="doc-item">
              <div className="doc-main">
                <span className="doc-title">{f.name}</span>
                <span className="doc-sub mono">
                  {f.path !== f.name ? `${f.path} · ` : ""}
                  {formatBytes(f.size_bytes)} · {timeAgo(new Date(f.modified_at).toISOString())}
                </span>
              </div>
              <div className="doc-actions">
                <Button onClick={() => previewAgentFile(g.agent_id, f)}>Preview</Button>
                <Button onClick={() => openPath(f.abs_path)}>Open location</Button>
                <Button variant="ghost" onClick={() => removeAgentFile(g.agent_id, f)}>Delete</Button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    ));
  };

  // ---- my documents (Evano workspace) ------------------------------------ //

  const showPreview = async (doc: DocumentInfo) => {
    setError(null);
    try {
      const detail: DocumentDetail = await backendApi.getDocument(doc.id);
      setPreview({ title: detail.title, content: detail.content });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't read the document.");
    }
  };

  const removeDocument = async (doc: DocumentInfo) => {
    if (!window.confirm(`Delete "${doc.title}"? This removes the file too.`)) return;
    setError(null);
    try {
      await backendApi.deleteDocument(doc.id);
      if (preview?.title === doc.title) setPreview(null);
      docsRes.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't delete the document.");
    }
  };

  const renderMyDocs = () => {
    if (docsRes.state === "checking") return <p className="muted">Loading documents…</p>;
    if (docsRes.state !== "ready") {
      return <p className="muted">Can&apos;t reach the engine — start it and refresh.</p>;
    }
    if (documents.length === 0) {
      return <p className="muted">Nothing here — chats saved with “Save as document” land in this list.</p>;
    }
    return (
      <ul className="doc-list">
        {documents.map((doc) => (
          <li key={doc.id} className="doc-item">
            <div className="doc-main">
              <span className="doc-title">{doc.title}</span>
              <span className="doc-sub mono">
                {doc.file_name} · {formatBytes(doc.size_bytes)}
                {doc.exists ? "" : " · file missing"}
              </span>
            </div>
            <div className="doc-actions">
              <Badge tone="neutral">{doc.file_type}</Badge>
              <Button onClick={() => showPreview(doc)}>Preview</Button>
              <Button onClick={() => openPath(doc.file_path)}>Open location</Button>
              <Button variant="ghost" onClick={() => removeDocument(doc)}>Delete</Button>
            </div>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="📄"
        title="Documents"
        subtitle="Everything your agents have written — reports, drafts, and team files, straight from their folders."
      />

      <div className="toolbar">
        <span className="muted">
          {agentDocsRes.state === "ready" && agentDocsRes.data?.ok
            ? `${agentDocsRes.data.agents.reduce((n, g) => n + g.files.length, 0)} agent file(s)`
            : "—"}
        </span>
        <div className="toolbar-actions">
          <Button onClick={refreshAll}>↻ Refresh</Button>
        </div>
      </div>

      {error ? <div className="chat-error" role="alert">{error}</div> : null}

      <p className="section-label">🤖 Agent documents</p>
      {renderAgentDocs()}

      <p className="section-label" style={{ marginTop: 18 }}>📁 My documents</p>
      {renderMyDocs()}

      {preview ? (
        <Card className="doc-preview">
          <div className="doc-preview-head">
            <h3>{preview.title}</h3>
            <Button variant="ghost" onClick={() => setPreview(null)}>Close</Button>
          </div>
          {preview.truncated ? (
            <p className="form-hint">Long file — showing the first part only. Use Open location for the full file.</p>
          ) : null}
          <pre className="doc-preview-content">{preview.content}</pre>
        </Card>
      ) : null}
    </div>
  );
}
