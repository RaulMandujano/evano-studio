import { useState, type FormEvent } from "react";
import { Button } from "../ui/Button";
import type { Agent, AgentCreate, ToolSpec } from "../../lib/api/types";

interface AgentFormProps {
  initial?: Agent | null;
  /** Pre-fill values for a NEW agent (e.g. from a template). Labels stay "create". */
  prefill?: Partial<Agent> | null;
  models: string[];
  defaultModel: string;
  tools: ToolSpec[];
  submitting?: boolean;
  error?: string | null;
  onSubmit: (data: AgentCreate) => void;
  onCancel: () => void;
}

// Safe, workspace-confined tools enabled by default on a brand-new agent so it
// works out of the box. Computer-control tools are NOT included (they require
// approval and must be opted into deliberately).
const DEFAULT_SAFE_TOOLS = [
  "create_folder",
  "create_text_file",
  "read_text_file",
  "list_files",
  "create_markdown_document",
  "create_word_document",
  "create_pdf_document",
  "search_workspace",
];

/** Create / edit form for an agent. Controlled, local state only. */
export function AgentForm({
  initial,
  prefill,
  models,
  defaultModel,
  tools,
  submitting,
  error,
  onSubmit,
  onCancel,
}: AgentFormProps) {
  const seed = initial ?? prefill ?? null;
  const [name, setName] = useState(seed?.name ?? "");
  const [modelName, setModelName] = useState(seed?.model_name ?? defaultModel);
  const [description, setDescription] = useState(seed?.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState(seed?.system_prompt ?? "");
  const [temperature, setTemperature] = useState(seed?.temperature ?? 0.7);
  const [isEnabled, setIsEnabled] = useState(seed?.is_enabled ?? true);
  const [knowledgeEnabled, setKnowledgeEnabled] = useState(seed?.knowledge_enabled ?? false);
  const [imageEnabled, setImageEnabled] = useState(seed?.image_enabled ?? false);
  // New blank agent → start with the safe workspace tools enabled. Templates and
  // edits use their own tool selection.
  const [enabledTools, setEnabledTools] = useState<string[]>(
    seed?.enabled_tools ?? DEFAULT_SAFE_TOOLS,
  );

  const toggleTool = (id: string) => {
    setEnabledTools((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id],
    );
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      name: name.trim(),
      model_name: modelName.trim(),
      description: description.trim(),
      system_prompt: systemPrompt,
      temperature,
      is_enabled: isEnabled,
      knowledge_enabled: knowledgeEnabled,
      image_enabled: imageEnabled,
      enabled_tools: enabledTools,
    });
  };

  const canSubmit = name.trim().length > 0 && modelName.trim().length > 0 && !submitting;

  return (
    <form className="agent-form" onSubmit={handleSubmit}>
      <h3>{initial ? "Edit agent" : "New agent"}</h3>

      <div className="form-row">
        <label htmlFor="agent-name">Name</label>
        <input
          id="agent-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Support Assistant"
          maxLength={120}
          required
        />
      </div>

      <div className="form-row">
        <label htmlFor="agent-model">Model</label>
        <input
          id="agent-model"
          list="agent-model-options"
          value={modelName}
          onChange={(e) => setModelName(e.target.value)}
          placeholder="e.g. gemma3:4b"
          required
        />
        <datalist id="agent-model-options">
          {models.map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>
        <p className="form-hint">Choose an installed model. Install more on the Models page.</p>
      </div>

      <div className="form-row">
        <label htmlFor="agent-desc">Description</label>
        <input
          id="agent-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What is this agent for?"
        />
      </div>

      <div className="form-row">
        <label htmlFor="agent-prompt">System prompt</label>
        <textarea
          id="agent-prompt"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          rows={5}
          placeholder="Instructions that define how this agent behaves…"
        />
      </div>

      <div className="form-row">
        <label htmlFor="agent-temp">Temperature: {temperature.toFixed(1)}</label>
        <input
          id="agent-temp"
          type="range"
          min={0}
          max={2}
          step={0.1}
          value={temperature}
          onChange={(e) => setTemperature(Number(e.target.value))}
        />
      </div>

      <div className="form-checks">
        <label>
          <input
            type="checkbox"
            checked={isEnabled}
            onChange={(e) => setIsEnabled(e.target.checked)}
          />
          Enabled
        </label>
        <label>
          <input
            type="checkbox"
            checked={knowledgeEnabled}
            onChange={(e) => setKnowledgeEnabled(e.target.checked)}
          />
          Knowledge base (RAG)
        </label>
        <label className="muted">
          <input
            type="checkbox"
            checked={imageEnabled}
            onChange={(e) => setImageEnabled(e.target.checked)}
          />
          Image generation (coming soon)
        </label>
      </div>

      <div className="form-tools">
        <p className="form-tools-label">Tools (deny-by-default)</p>
        {tools.length === 0 ? (
          <p className="form-hint">No tools available.</p>
        ) : (
          <ul className="tool-toggle-list">
            {tools.map((tool) => (
              <li key={tool.id} className="tool-toggle">
                <label>
                  <input
                    type="checkbox"
                    checked={enabledTools.includes(tool.id)}
                    onChange={() => toggleTool(tool.id)}
                  />
                  <span className="tool-toggle-name">{tool.name}</span>
                </label>
                <span className="tool-toggle-desc">{tool.description}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      <div className="form-actions">
        <Button type="submit" variant="primary" disabled={!canSubmit}>
          {submitting ? "Saving…" : initial ? "Save changes" : "Create agent"}
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
