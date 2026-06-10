import { useCallback, useEffect, useState } from "react";
import { Card } from "../ui/Card";
import { Badge, type BadgeTone } from "../ui/Badge";
import { Button } from "../ui/Button";
import { backendApi } from "../../lib/api/client";
import type { ServiceStatus } from "../../../../shared/api";

const OLLAMA_INSTALL_URL = "https://ollama.com/download";
const COMFYUI_SETUP_URL = "https://github.com/comfyanonymous/ComfyUI#installing";

type SubStatus = { tone: BadgeTone; label: string };

export function ServiceManager() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [ollama, setOllama] = useState<SubStatus>({ tone: "neutral", label: "—" });
  const [chroma, setChroma] = useState<SubStatus>({ tone: "neutral", label: "—" });
  const [comfyui, setComfyui] = useState<SubStatus>({ tone: "neutral", label: "—" });
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const available = typeof window !== "undefined" && Boolean(window.evano?.services);

  const load = useCallback(async () => {
    if (!available) return;
    try {
      setStatus(await window.evano.services.getStatus());
    } catch {
      /* ignore */
    }
    // Subsystem statuses (best-effort; need the backend reachable).
    try {
      const o = await backendApi.getOllamaStatus();
      setOllama(
        o.status === "running"
          ? { tone: "ok", label: "Running" }
          : { tone: "pending", label: "Not running" },
      );
    } catch {
      setOllama({ tone: "neutral", label: "Unknown" });
    }
    try {
      const k = await backendApi.getKnowledgeStatus();
      setChroma(k.available ? { tone: "ok", label: "Available" } : { tone: "danger", label: "Unavailable" });
    } catch {
      setChroma({ tone: "neutral", label: "Unknown" });
    }
    try {
      const c = await backendApi.getComfyUIStatus();
      setComfyui(
        !c.enabled
          ? { tone: "neutral", label: "Disabled" }
          : c.reachable
            ? { tone: "ok", label: "Reachable" }
            : { tone: "danger", label: "Unreachable" },
      );
    } catch {
      setComfyui({ tone: "neutral", label: "Unknown" });
    }
  }, [available]);

  useEffect(() => {
    void load();
  }, [load]);

  const act = async (fn: () => Promise<{ ok: boolean; reason?: string; error?: string }>, okMsg: string) => {
    setBusy(true);
    setNote(null);
    try {
      const result = await fn();
      if (result.ok) setNote(okMsg);
      else if (result.reason === "not_configured")
        setNote("Auto-start isn't configured. Start the backend manually (see docs).");
      else if (result.reason === "not_managed")
        setNote("Evano Studio didn't start this backend, so it won't stop it.");
      else setNote(result.error ?? "Action failed.");
      // Give the backend a moment, then refresh.
      setTimeout(() => void load(), 800);
    } finally {
      setBusy(false);
    }
  };

  // Open the workspace the backend is actually configured to use (single source
  // of truth), not the Electron default. Falls back to the default opener.
  const openConfiguredWorkspace = async () => {
    try {
      const ws = await backendApi.getWorkspaceStatus();
      const result = await window.evano.services.openWorkspacePath(ws.path);
      if (!result.ok) setNote(result.error ?? "Couldn't open the workspace.");
    } catch {
      await window.evano.services.openWorkspace();
    }
  };

  if (!available) {
    return (
      <Card>
        <h3 className="settings-section-title">Local services</h3>
        <p className="muted">Service management is only available in the desktop app.</p>
      </Card>
    );
  }

  const backend = status?.backend;

  return (
    <Card>
      <div className="env-card-head">
        <h3 className="settings-section-title">Local services</h3>
        <Button onClick={() => void load()} disabled={busy}>↻ Refresh</Button>
      </div>

      <ul className="service-list">
        <li className="service-row">
          <div>
            <span className="service-name">Agent Engine</span>
            <span className="service-sub mono">{backend?.url ?? "—"}</span>
          </div>
          <div className="service-actions">
            <Badge tone={backend?.reachable ? "ok" : "danger"} dot>
              {backend?.reachable ? "Running" : "Offline"}
            </Badge>
            <Button
              onClick={() => act(() => window.evano.services.startBackend(), "Backend starting…")}
              disabled={busy || backend?.reachable || !backend?.canStart}
              title={backend?.canStart ? undefined : "Auto-start not configured, or already running"}
            >
              Start
            </Button>
            <Button
              onClick={() => act(() => window.evano.services.stopBackend(), "Backend stopping…")}
              disabled={busy || !backend?.managed}
              title={backend?.managed ? undefined : "Only a backend started by Evano Studio can be stopped"}
            >
              Stop
            </Button>
          </div>
        </li>

        <li className="service-row">
          <div>
            <span className="service-name">Ollama</span>
            <span className="service-sub">Local AI runtime</span>
          </div>
          <div className="service-actions">
            <Badge tone={ollama.tone} dot>{ollama.label}</Badge>
            <Button onClick={() => window.evano.services.openExternal(OLLAMA_INSTALL_URL)}>
              Get Ollama
            </Button>
          </div>
        </li>

        <li className="service-row">
          <div>
            <span className="service-name">ChromaDB</span>
            <span className="service-sub">Local knowledge base</span>
          </div>
          <div className="service-actions">
            <Badge tone={chroma.tone} dot>{chroma.label}</Badge>
          </div>
        </li>

        <li className="service-row">
          <div>
            <span className="service-name">ComfyUI</span>
            <span className="service-sub">Optional image generation</span>
          </div>
          <div className="service-actions">
            <Badge tone={comfyui.tone} dot>{comfyui.label}</Badge>
            <Button onClick={() => window.evano.services.openExternal(COMFYUI_SETUP_URL)}>
              Setup docs
            </Button>
          </div>
        </li>
      </ul>

      <div className="form-actions" style={{ marginTop: 14 }}>
        <Button onClick={openConfiguredWorkspace}>📁 Open workspace</Button>
        <Button onClick={() => window.evano.services.openLogs()}>📋 Open logs</Button>
      </div>

      {note ? <p className="settings-ok">{note}</p> : null}
    </Card>
  );
}
