import { useState } from "react";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { backendApi } from "../../lib/api/client";
import { statusTone } from "../../lib/routines";
import type { Agent, ImageGeneration } from "../../lib/api/types";

interface AgentImagePanelProps {
  agent: Agent;
  comfyuiReachable: boolean;
}

/** In-chat image workflow: craft a prompt with the agent, then (optionally)
 *  generate via local ComfyUI. Nothing generates without an explicit click. */
export function AgentImagePanel({ agent, comfyuiReachable }: AgentImagePanelProps) {
  const [idea, setIdea] = useState("");
  const [prompt, setPrompt] = useState("");
  const [negative, setNegative] = useState("");
  const [creating, setCreating] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImageGeneration | null>(null);

  const canGenerate = agent.image_enabled && comfyuiReachable && prompt.trim().length > 0;

  const createPrompt = async () => {
    if (!idea.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const res = await backendApi.createAgentImagePrompt(agent.id, { idea: idea.trim() });
      if (res.ok && res.prompt) setPrompt(res.prompt);
      else setError(res.message ?? "Couldn't create a prompt.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't create a prompt.");
    } finally {
      setCreating(false);
    }
  };

  const generate = async () => {
    if (!canGenerate) return;
    setGenerating(true);
    setError(null);
    setResult(null);
    try {
      const record = await backendApi.generateAgentImage(agent.id, {
        prompt: prompt.trim(),
        negative_prompt: negative.trim(),
      });
      setResult(record);
      if (record.status !== "success") setError(record.error ?? "Generation failed.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed.");
    } finally {
      setGenerating(false);
    }
  };

  const openLocation = async (path: string) => {
    const reveal = window.evano?.documents?.revealPath;
    if (reveal) await reveal(path);
  };

  return (
    <div className="image-panel">
      <h4 className="settings-section-title">Image tools · {agent.name}</h4>

      <div className="form-row">
        <label htmlFor="img-idea">Idea</label>
        <input
          id="img-idea"
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="Describe an image idea…"
        />
      </div>
      <div className="form-actions">
        <Button onClick={createPrompt} disabled={creating || !idea.trim()}>
          {creating ? "Creating…" : "✨ Create image prompt"}
        </Button>
      </div>

      <div className="form-row" style={{ marginTop: 12 }}>
        <label htmlFor="img-prompt2">Prompt (editable)</label>
        <textarea
          id="img-prompt2"
          rows={3}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="The agent's image prompt appears here — edit before generating."
        />
      </div>
      <div className="form-row">
        <label htmlFor="img-neg2">Negative (optional)</label>
        <input id="img-neg2" value={negative} onChange={(e) => setNegative(e.target.value)} />
      </div>

      <div className="form-actions">
        <Button
          variant="primary"
          onClick={generate}
          disabled={!canGenerate || generating}
          title={canGenerate ? undefined : "Needs image-enabled agent + reachable ComfyUI"}
        >
          {generating ? "Generating…" : "Generate with ComfyUI"}
        </Button>
      </div>

      {!agent.image_enabled ? (
        <p className="form-hint">This agent isn&apos;t image-enabled. Enable it in the agent settings.</p>
      ) : !comfyuiReachable ? (
        <p className="form-hint">ComfyUI isn&apos;t reachable. Configure it on the Images page.</p>
      ) : null}

      {result && result.status === "success" && result.output_path ? (
        <div className="image-result">
          <Badge tone={statusTone(result.status)} dot>
            {result.status}
          </Badge>
          <Button onClick={() => openLocation(result.output_path as string)}>Open location</Button>
        </div>
      ) : null}

      {error ? <p className="form-error">{error}</p> : null}
    </div>
  );
}
