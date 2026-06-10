import { useState, type FormEvent } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import type {
  KnowledgeDocument,
  KnowledgeSearchResult,
  KnowledgeStatus,
} from "../lib/api/types";

export function KnowledgeBaseView() {
  const statusRes = useBackendResource<KnowledgeStatus>(backendApi.getKnowledgeStatus, "kb-status");
  const docsRes = useBackendResource<KnowledgeDocument[]>(backendApi.getKnowledgeDocuments, "kb-docs");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncNote, setSyncNote] = useState<string | null>(null);

  const syncToAgents = async () => {
    setSyncing(true);
    setSyncNote(null);
    setError(null);
    try {
      const r = await backendApi.syncKnowledgeToAgents();
      setSyncNote(r.ok ? `✓ ${r.message}` : r.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sync failed.");
    } finally {
      setSyncing(false);
    }
  };

  const status = statusRes.data;
  const documents = docsRes.data ?? [];
  const available = status?.available ?? false;

  const refreshAll = () => {
    statusRes.refresh();
    docsRes.refresh();
  };

  const importFile = async () => {
    setError(null);
    const picker = window.evano?.knowledge?.pickTextFile;
    if (!picker) {
      setError("File import isn't available in this environment.");
      return;
    }
    const picked = await picker();
    if (picked.canceled) return;
    if (!picked.ok || !picked.content || !picked.fileName) {
      setError(picked.error ?? "Couldn't read the file.");
      return;
    }
    setBusy(true);
    try {
      const title = picked.fileName.replace(/\.(txt|md|markdown)$/i, "");
      const fileType = picked.fileName.toLowerCase().endsWith(".txt") ? "txt" : "md";
      await backendApi.importKnowledgeDocument({
        title,
        file_name: picked.fileName,
        content: picked.content,
        file_type: fileType,
        source_path: picked.path ?? "",
      });
      refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed.");
    } finally {
      setBusy(false);
    }
  };

  const removeDocument = async (doc: KnowledgeDocument) => {
    if (!window.confirm(`Remove "${doc.title}" from the knowledge base?`)) return;
    setError(null);
    try {
      await backendApi.deleteKnowledgeDocument(doc.id);
      refreshAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed.");
    }
  };

  const runSearch = async (event: FormEvent) => {
    event.preventDefault();
    const q = query.trim();
    if (!q || searching) return;
    setSearching(true);
    setError(null);
    try {
      const response = await backendApi.searchKnowledge(q, 5);
      if (response.ok) setResults(response.results);
      else {
        setResults([]);
        setError(response.message ?? "Search failed.");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed.");
    } finally {
      setSearching(false);
    }
  };

  const renderStatus = () => {
    if (statusRes.state === "checking") return <p className="muted">Checking knowledge base…</p>;
    if (statusRes.state !== "ready" || !status) {
      return (
        <Card className="notice-card">
          <h3>Can&apos;t reach the local backend</h3>
          <p className="muted">Start the Agent Engine, then refresh.</p>
        </Card>
      );
    }
    return (
      <section className="engine-panel">
        <div className="engine-panel-head">
          <div className="engine-panel-title">
            <span className="engine-panel-icon" aria-hidden="true">📚</span>
            <div>
              <h3>ChromaDB (local)</h3>
              <p className="engine-panel-help">
                {available
                  ? "Local vector store is ready. Nothing leaves your machine."
                  : "Local setup needed — see the message below."}
              </p>
            </div>
          </div>
          <div className="engine-panel-actions">
            <Badge tone={available ? "ok" : "danger"} dot>
              {available ? "Available" : "Unavailable"}
            </Badge>
            <Button onClick={syncToAgents} disabled={syncing || !available}>
              {syncing ? "Syncing…" : "⇄ Sync to agents"}
            </Button>
            <Button onClick={refreshAll}>↻ Refresh</Button>
          </div>
        </div>
        <dl className="engine-grid">
          <div><dt>Embedding</dt><dd className="mono">{status.embedding}</dd></div>
          <div><dt>Collection</dt><dd className="mono">{status.collection}</dd></div>
          <div><dt>Documents</dt><dd className="mono">{status.document_count}</dd></div>
          <div><dt>Chunks</dt><dd className="mono">{status.chunk_count}</dd></div>
        </dl>
        <p className="form-hint">
          Documents auto-sync into each agent&apos;s memory, so they also know this on Discord and
          in delegated Org Chart tasks. Use Sync if you changed agents recently.
        </p>
        {syncNote ? <p className="settings-ok">{syncNote}</p> : null}
        {!available && status.message ? <p className="engine-message">{status.message}</p> : null}
      </section>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="📚"
        title="Knowledge Base"
        subtitle="Import .txt/.md files into a local ChromaDB knowledge base. Local embeddings, no cloud."
        badge={<Badge tone="alpha">Live</Badge>}
      />

      {renderStatus()}

      {error ? <div className="chat-error" role="alert">{error}</div> : null}

      <div className="toolbar">
        <span className="muted">{documents.length} document(s)</span>
        <Button variant="primary" onClick={importFile} disabled={busy || !available}>
          {busy ? "Importing…" : "+ Import .txt/.md"}
        </Button>
      </div>

      {documents.length === 0 ? (
        <p className="muted">
          {available ? "No documents yet. Import a .txt or .md file to get started." : ""}
        </p>
      ) : (
        <ul className="doc-list">
          {documents.map((doc) => (
            <li key={doc.id} className="doc-item">
              <div className="doc-main">
                <span className="doc-title">{doc.title}</span>
                <span className="doc-sub mono">
                  {doc.file_name} · {doc.chunk_count} chunk(s)
                </span>
              </div>
              <div className="doc-actions">
                <Button variant="ghost" onClick={() => removeDocument(doc)}>Delete</Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <h2 className="section-label">Search</h2>
      <form className="kb-search" onSubmit={runSearch}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search your knowledge base…"
          disabled={!available}
        />
        <Button type="submit" variant="primary" disabled={!available || searching || !query.trim()}>
          {searching ? "Searching…" : "Search"}
        </Button>
      </form>

      {results !== null ? (
        results.length === 0 ? (
          <p className="muted">No matches.</p>
        ) : (
          <ul className="kb-results">
            {results.map((r, i) => (
              <li key={i} className="kb-result">
                <div className="kb-result-head">
                  <span className="mono">{r.title ?? r.file_name ?? "source"}</span>
                  {r.distance !== null ? (
                    <span className="muted">distance {r.distance.toFixed(3)}</span>
                  ) : null}
                </div>
                <p className="kb-result-text">{r.text}</p>
              </li>
            ))}
          </ul>
        )
      ) : null}
    </div>
  );
}
