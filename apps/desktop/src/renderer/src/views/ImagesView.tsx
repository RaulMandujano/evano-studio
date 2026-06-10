import { useEffect, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { statusTone } from "../lib/routines";
import { formatDateTime } from "../lib/routines";
import type { Agent, ComfyUIStatus, ImageGeneration } from "../lib/api/types";

export function ImagesView() {
  const statusRes = useBackendResource<ComfyUIStatus>(backendApi.getComfyUIStatus);
  const imagesRes = useBackendResource<ImageGeneration[]>(backendApi.getImages);
  const agentsRes = useBackendResource<Agent[]>(backendApi.getAgents);

  const status = statusRes.data;
  const images = imagesRes.data ?? [];
  const agentName = (id: number | null) =>
    id == null ? null : (agentsRes.data?.find((a) => a.id === id)?.name ?? `Agent #${id}`);

  // Settings form (initialized from status once loaded).
  const [baseUrl, setBaseUrl] = useState("");
  const [enabled, setEnabled] = useState(false);
  const [workflowPath, setWorkflowPath] = useState("");
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);

  const [prompt, setPrompt] = useState("");
  const [negative, setNegative] = useState("");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (status && !settingsLoaded) {
      setBaseUrl(status.base_url);
      setEnabled(status.enabled);
      setWorkflowPath(status.default_workflow_path);
      setSettingsLoaded(true);
    }
  }, [status, settingsLoaded]);

  const refreshAll = () => {
    statusRes.refresh();
    imagesRes.refresh();
  };

  const saveSettings = async () => {
    setSavingSettings(true);
    setError(null);
    setNotice(null);
    try {
      await backendApi.updateComfyUISettings({
        base_url: baseUrl.trim(),
        enabled,
        default_workflow_path: workflowPath.trim(),
      });
      statusRes.refresh();
      setNotice("ComfyUI settings saved.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't save settings.");
    } finally {
      setSavingSettings(false);
    }
  };

  const suggestPrompt = async () => {
    setError(null);
    try {
      const result = await backendApi.testTool("generate_image_prompt", {
        subject: prompt.trim() || "a scenic landscape",
      });
      const composed = (result.result as { prompt?: string } | null)?.prompt;
      if (result.ok && composed) setPrompt(composed);
      else setError(result.message ?? "Couldn't generate a prompt.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't generate a prompt.");
    }
  };

  const generate = async () => {
    if (!prompt.trim()) return;
    setGenerating(true);
    setError(null);
    setNotice(null);
    try {
      const record = await backendApi.generateImage({
        prompt: prompt.trim(),
        negative_prompt: negative.trim(),
      });
      imagesRes.refresh();
      if (record.status === "success") setNotice("Image generated and saved to your workspace.");
      else setError(record.error ?? "Image generation failed.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Image generation failed.");
    } finally {
      setGenerating(false);
    }
  };

  const openLocation = async (path: string) => {
    const reveal = window.evano?.documents?.revealPath;
    if (reveal) await reveal(path);
  };

  const canGenerate = Boolean(status?.enabled && status?.reachable) && !generating;

  return (
    <div className="view">
      <PageHeader
        icon="🎨"
        title="Images"
        subtitle="Generate images locally through your own ComfyUI. Optional — nothing leaves your machine."
        badge={<Badge tone="alpha">Live</Badge>}
      />

      {/* Status + settings */}
      <section className="engine-panel">
        <div className="engine-panel-head">
          <div className="engine-panel-title">
            <span className="engine-panel-icon" aria-hidden="true">🎨</span>
            <div>
              <h3>ComfyUI (local)</h3>
              <p className="engine-panel-help">
                {status?.enabled
                  ? status?.reachable
                    ? "Connected and ready."
                    : "Enabled but not reachable — start ComfyUI and check the URL."
                  : "Disabled. Configure and enable it below to generate images."}
              </p>
            </div>
          </div>
          <div className="engine-panel-actions">
            <Badge tone={status?.reachable ? "ok" : status?.enabled ? "danger" : "neutral"} dot>
              {status ? (status.reachable ? "Reachable" : status.enabled ? "Unreachable" : "Disabled") : "—"}
            </Badge>
            <Button onClick={refreshAll}>↻ Refresh</Button>
          </div>
        </div>

        <div className="form-row" style={{ marginTop: 14 }}>
          <label htmlFor="cf-url">ComfyUI URL</label>
          <input
            id="cf-url"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="http://127.0.0.1:8188"
            disabled={!settingsLoaded}
          />
        </div>
        <div className="form-row">
          <label htmlFor="cf-workflow">Workflow file (optional, API format)</label>
          <input
            id="cf-workflow"
            value={workflowPath}
            onChange={(e) => setWorkflowPath(e.target.value)}
            placeholder="/path/to/workflow_api.json  (uses a built-in default if blank)"
            disabled={!settingsLoaded}
          />
        </div>
        <div className="form-checks">
          <label>
            <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
            Enable ComfyUI image generation
          </label>
        </div>
        <div className="form-actions">
          <Button variant="primary" onClick={saveSettings} disabled={!settingsLoaded || savingSettings}>
            {savingSettings ? "Saving…" : "Save ComfyUI settings"}
          </Button>
        </div>
        {status && !status.reachable && status.message ? (
          <p className="engine-message">{status.message}</p>
        ) : null}
      </section>

      {/* Prompt + generate */}
      <Card className="card-spaced">
        <h3 className="settings-section-title">Generate an image</h3>
        <div className="form-row">
          <label htmlFor="img-prompt">Prompt</label>
          <textarea
            id="img-prompt"
            rows={3}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want…"
          />
        </div>
        <div className="form-row">
          <label htmlFor="img-negative">Negative prompt (optional)</label>
          <input
            id="img-negative"
            value={negative}
            onChange={(e) => setNegative(e.target.value)}
            placeholder="What to avoid…"
          />
        </div>
        <div className="form-actions">
          <Button onClick={suggestPrompt} disabled={generating}>
            ✨ Suggest prompt
          </Button>
          <Button
            variant="primary"
            onClick={generate}
            disabled={!canGenerate || !prompt.trim()}
            title={canGenerate ? undefined : "Enable and connect ComfyUI first"}
          >
            {generating ? "Generating…" : "Generate image"}
          </Button>
        </div>
        {!status?.enabled || !status?.reachable ? (
          <p className="form-hint">
            Generation needs ComfyUI enabled and reachable. You can still write and suggest prompts.
          </p>
        ) : null}
        {notice ? <p className="settings-ok">{notice}</p> : null}
        {error ? <p className="form-error">{error}</p> : null}
      </Card>

      {/* History */}
      <h2 className="section-label">History</h2>
      {imagesRes.state === "checking" ? (
        <p className="muted">Loading…</p>
      ) : images.length === 0 ? (
        <p className="muted">No images yet.</p>
      ) : (
        <ul className="doc-list">
          {images.map((img) => (
            <li key={img.id} className="doc-item">
              <div className="doc-main">
                <span className="doc-title">{img.prompt}</span>
                <span className="doc-sub mono">
                  {formatDateTime(img.created_at)}
                  {agentName(img.created_by_agent_id) ? ` · by ${agentName(img.created_by_agent_id)}` : ""}
                  {img.error ? ` · ${img.error}` : ""}
                </span>
              </div>
              <div className="doc-actions">
                <Badge tone={statusTone(img.status)}>{img.status}</Badge>
                {img.output_path ? (
                  <Button onClick={() => openLocation(img.output_path as string)}>Open location</Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
