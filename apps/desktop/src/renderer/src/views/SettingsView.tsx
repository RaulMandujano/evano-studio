import { useEffect, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ServiceManager } from "../components/settings/ServiceManager";
import { DiscordSettings } from "../components/settings/DiscordSettings";
import { backendApi } from "../lib/api/client";
import type { WorkspaceStatus } from "../lib/api/types";

export function SettingsView() {
  const [status, setStatus] = useState<WorkspaceStatus | null>(null);
  const [workspace, setWorkspace] = useState<string>("");
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const ws = await backendApi.getWorkspaceStatus();
      setStatus(ws);
      setWorkspace(ws.configured ? ws.path : "");
      setLoaded(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't load settings.");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const browse = async () => {
    const picker = window.evano?.system?.pickFolder;
    if (!picker) {
      setError("Folder picker isn't available in this environment.");
      return;
    }
    const result = await picker();
    if (result.ok && result.path) setWorkspace(result.path);
  };

  const save = async () => {
    await configure(workspace.trim(), "saved");
  };

  const reset = async () => {
    setWorkspace("");
    await configure("", "reset");
  };

  const configure = async (path: string, kind: "saved" | "reset") => {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const ws = await backendApi.configureWorkspace(path);
      setStatus(ws);
      setWorkspace(ws.configured ? ws.path : "");
      setMessage(
        kind === "reset"
          ? "Workspace reset to the default location. Standard folders created."
          : "Workspace saved. Standard folders created; documents and file tools will use it.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't update the workspace.");
    } finally {
      setSaving(false);
    }
  };

  // Open the *configured* workspace (single source of truth = the backend),
  // not the Electron default. Falls back to the default opener if unavailable.
  const openFolder = () => {
    const path = status?.path;
    if (path && window.evano?.services?.openWorkspacePath) {
      void window.evano.services.openWorkspacePath(path);
    } else {
      void window.evano?.services?.openWorkspace?.();
    }
  };

  return (
    <div className="view">
      <PageHeader
        icon="⚙️"
        title="Settings"
        subtitle="Manage local services and your workspace folder."
        badge={<Badge tone="alpha">Live</Badge>}
      />

      <ServiceManager />

      <div style={{ marginTop: 18 }} />

      <Card>
        <h3 className="settings-section-title">Workspace folder</h3>
        <p className="muted form-hint">
          The only place documents and file tools can read or write. Saving creates the standard
          folders (Documents, Images, KnowledgeBase, Projects, Reports, Logs). Leave blank to use
          the default location.
        </p>

        <div className="form-row">
          <label htmlFor="workspace">Workspace path</label>
          <div className="workspace-row">
            <input
              id="workspace"
              value={workspace}
              onChange={(e) => setWorkspace(e.target.value)}
              placeholder={status?.default_path || "Default workspace"}
              disabled={!loaded}
            />
            <Button onClick={browse} disabled={!loaded}>
              Browse…
            </Button>
          </div>
          <p className="form-hint">
            Current: <span className="mono">{status?.path || "—"}</span>{" "}
            {status ? (
              <Badge tone={status.ready ? "ok" : "pending"} dot>
                {status.ready ? "Ready" : status.is_default ? "Default" : "Incomplete"}
              </Badge>
            ) : null}
          </p>
        </div>

        {status && status.subdirs.length > 0 ? (
          <ul className="workspace-subdirs">
            {status.subdirs.map((d) => (
              <li key={d.name} className={d.exists ? "subdir--ok" : "subdir--missing"}>
                <span aria-hidden="true">{d.exists ? "✓" : "○"}</span> {d.name}
              </li>
            ))}
          </ul>
        ) : null}

        <div className="form-actions">
          <Button variant="primary" onClick={save} disabled={!loaded || saving}>
            {saving ? "Saving…" : "Save workspace"}
          </Button>
          <Button onClick={openFolder} disabled={!loaded || saving}>
            Open folder
          </Button>
          <Button onClick={reset} disabled={!loaded || saving}>
            Reset to default
          </Button>
        </div>

        {message ? <p className="settings-ok">{message}</p> : null}
        {error ? <p className="form-error">{error}</p> : null}
      </Card>

      <DiscordSettings />
    </div>
  );
}
