/**
 * AFM — Agent File Management.
 *
 * One tidy folder for everything agents create. Picking a root (or keeping the
 * Evano default) points every OpenClaw agent's REAL workspace at
 * <root>/Agents/<Name> and files team runs under <root>/Teams/<Team>/<Member>.
 * No copies, no duplicates — the agents genuinely live there.
 */
import { useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";
import type { AfmStatus } from "../lib/api/types";

export function AfmView() {
  const navigate = useNavigate();
  const res = useBackendResource<AfmStatus>(backendApi.getAfmStatus);

  const [customRoot, setCustomRoot] = useState<string | null>(null);
  const [useDefault, setUseDefault] = useState(true);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [noteOk, setNoteOk] = useState(false);

  const status = res.data;
  const allManaged = !!status?.ok && status.agents.length > 0 && status.agents.every((a) => a.managed);

  const pickFolder = async () => {
    const picker = window.evano?.system?.pickFolder;
    if (!picker) {
      setNote("Folder picking isn't available in this environment.");
      setNoteOk(false);
      return;
    }
    const picked = await picker();
    if (!picked.canceled && picked.path) {
      setCustomRoot(picked.path);
      setUseDefault(false);
    }
  };

  const organize = async () => {
    setBusy(true);
    setNote(null);
    try {
      const r = await backendApi.applyAfm(useDefault ? null : customRoot);
      setNoteOk(r.ok);
      setNote(r.message);
      if (r.ok) res.refresh();
    } catch (e) {
      setNoteOk(false);
      setNote(e instanceof Error ? e.message : "Couldn't organize the folders.");
    } finally {
      setBusy(false);
    }
  };

  const openFolder = async (path: string) => {
    const reveal = window.evano?.documents?.revealPath;
    if (reveal) await reveal(path);
  };

  const renderTree = () => {
    if (!status?.ok) return null;
    return (
      <Card className="card-spaced">
        <div className="afm-tree-head">
          <h3 className="settings-section-title">Your structure</h3>
          <Button onClick={() => openFolder(status.root)}>📂 Open root folder</Button>
        </div>
        <div className="afm-tree">
          <div className="afm-node afm-node--root">
            <span className="afm-node-icon">🗂️</span>
            <span className="afm-node-name mono">{status.root}</span>
            {status.is_default ? <Badge tone="info" dot>Evano default</Badge> : <Badge tone="ok" dot>Custom</Badge>}
          </div>

          <div className="afm-branch">
            <div className="afm-node afm-node--dir">
              <span className="afm-node-icon">📁</span>
              <span className="afm-node-name">Agents</span>
              <span className="afm-node-hint muted">one home folder per agent — everything they create lands here</span>
            </div>
            <div className="afm-branch">
              {status.agents.map((a) => (
                <div key={a.agent_id} className="afm-node">
                  <span className="afm-node-icon">{a.emoji || "🤖"}</span>
                  <span className="afm-node-name">{a.name}</span>
                  {a.managed ? (
                    <Badge tone="ok" dot>In place</Badge>
                  ) : (
                    <Badge tone="pending" dot>Will move here</Badge>
                  )}
                  {a.managed ? (
                    <button type="button" className="afm-node-open" onClick={() => openFolder(a.workspace)}>
                      open
                    </button>
                  ) : null}
                </div>
              ))}
            </div>

            <div className="afm-node afm-node--dir">
              <span className="afm-node-icon">📁</span>
              <span className="afm-node-name">Teams</span>
              <span className="afm-node-hint muted">each team files its runs here — one subfolder per member</span>
            </div>
            <div className="afm-branch">
              {status.teams.length === 0 ? (
                <div className="afm-node afm-node--empty">
                  <span className="afm-node-icon">·</span>
                  <span className="afm-node-hint muted">
                    No teams yet — create one in <button type="button" className="afm-link" onClick={() => navigate("teams")}>Teams</button>
                  </span>
                </div>
              ) : (
                status.teams.map((t) => (
                  <div key={t.name} className="afm-team">
                    <div className="afm-node">
                      <span className="afm-node-icon">🤝</span>
                      <span className="afm-node-name">{t.name}</span>
                      {t.exists ? (
                        <button type="button" className="afm-node-open" onClick={() => openFolder(t.folder)}>
                          open
                        </button>
                      ) : null}
                    </div>
                    <div className="afm-branch">
                      {t.members.map((m) => (
                        <div key={m} className="afm-node afm-node--small">
                          <span className="afm-node-icon">👤</span>
                          <span className="afm-node-name">{m}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </Card>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="🗂️"
        title="AFM"
        subtitle="Agent File Management — one tidy folder for everything your agents create."
      />

      {res.state === "checking" ? <p className="muted">Checking your agents&apos; folders…</p> : null}

      {res.state === "ready" && status && !status.ok ? (
        <Card className="notice-card">
          <h3>OpenClaw isn&apos;t ready yet</h3>
          <p className="muted">{status.message || "Finish the setup first."}</p>
          <div className="form-actions"><Button variant="primary" onClick={() => navigate("openclaw")}>Go to setup</Button></div>
        </Card>
      ) : null}

      {status?.ok ? (
        <Card className="card-spaced afm-setup">
          <h3 className="settings-section-title">
            {allManaged ? "✅ Everything is organized" : "Where should your agents keep their files?"}
          </h3>
          {!allManaged ? (
            <p className="muted">
              Pick a home folder. Each agent gets its own folder inside, and team runs are filed
              automatically — easy to find, easy to back up.
            </p>
          ) : (
            <p className="muted">
              New agents and team runs land in this structure automatically. You can move it any time.
            </p>
          )}

          <div className="afm-choices">
            <button
              type="button"
              className={`afm-choice ${useDefault ? "is-active" : ""}`}
              onClick={() => setUseDefault(true)}
            >
              <span className="afm-choice-icon">🏠</span>
              <span className="afm-choice-title">Evano default</span>
              <span className="afm-choice-desc muted">Your Evano workspace folder — zero decisions.</span>
            </button>
            <button
              type="button"
              className={`afm-choice ${!useDefault ? "is-active" : ""}`}
              onClick={pickFolder}
            >
              <span className="afm-choice-icon">📂</span>
              <span className="afm-choice-title">{customRoot ? "Custom folder" : "Choose a folder…"}</span>
              <span className="afm-choice-desc muted mono">
                {customRoot ?? "Documents, Desktop, an external drive — anywhere."}
              </span>
            </button>
          </div>

          <div className="form-actions">
            <Button variant="primary" onClick={organize} disabled={busy}>
              {busy ? "Organizing…" : allManaged ? "Re-apply / move here" : "✨ Organize my agents"}
            </Button>
          </div>
          <p className="form-hint">
            Moves each agent&apos;s real folder (briefly restarting the gateway if it&apos;s running).
            Nothing is copied or duplicated.
          </p>
        </Card>
      ) : null}

      {note ? <p className={noteOk ? "settings-ok" : "form-error"}>{note}</p> : null}

      {renderTree()}
    </div>
  );
}
