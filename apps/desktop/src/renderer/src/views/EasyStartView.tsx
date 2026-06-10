import { useEffect, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SetupStep, type SetupStepProps, type StepState } from "../components/setup/SetupStep";
import { RecommendedSetup } from "../components/setup/RecommendedSetup";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";
import type { SetupStatus } from "../lib/api/types";

const OLLAMA_DOWNLOAD = "https://ollama.com/download";

/**
 * Easy Start — the onboarding center. Reads the aggregated /setup/status and
 * renders a guided checklist with visual progress, so a new user can get from
 * zero to a working local AI workforce without the terminal.
 */
export function EasyStartView() {
  const setup = useBackendResource<SetupStatus>(backendApi.getSetupStatus);
  const navigate = useNavigate();
  const [retries, setRetries] = useState(0);

  const openOllama = () => void window.evano?.services?.openExternal(OLLAMA_DOWNLOAD);

  // On first launch the bundled backend takes a few seconds to start. While it's
  // not reachable, quietly retry so the page comes alive on its own (no clicking).
  const offline = setup.state === "offline" || setup.state === "error";
  useEffect(() => {
    if (!offline || retries >= 12) return;
    const t = setTimeout(() => {
      setRetries((r) => r + 1);
      setup.refresh();
    }, 2500);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offline, retries]);

  const renderBody = () => {
    if (setup.state === "checking") {
      return <p className="muted">Checking your setup…</p>;
    }
    if (setup.state !== "ready" || !setup.data) {
      return (
        <Card className="notice-card">
          <h3>Starting Evano…</h3>
          <p className="muted">
            {retries < 12
              ? "The local engine is starting up — this can take a few seconds on first launch."
              : "The Agent Engine isn't responding. Make sure it's running, then retry."}
          </p>
          <div className="form-actions">
            <Button variant="primary" onClick={() => { setRetries(0); setup.refresh(); }}>
              Retry now
            </Button>
          </div>
        </Card>
      );
    }

    const s = setup.data;
    const steps = buildSteps(s, { navigate, openOllama });

    // "Ready" is derived from the required steps (optional ones don't block).
    const required = steps.filter((step) => step.required);
    const doneCount = required.filter((step) => step.state === "ok").length;
    const allReady = doneCount === required.length;
    const percent = Math.round((doneCount / required.length) * 100);

    return (
      <>
        <Card className="setup-progress-card">
          <div className="setup-progress-head">
            <div>
              <h3 className="setup-progress-title">
                {allReady ? "✓ System operational" : "Setup progress"}
              </h3>
              <p className="muted">
                {doneCount} of {required.length} required steps complete
                {allReady ? " — you're ready to put your agents to work." : "."}
              </p>
            </div>
            <Button onClick={setup.refresh}>Refresh</Button>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${percent}%` }} />
          </div>
        </Card>

        <RecommendedSetup status={s} onChanged={setup.refresh} />

        <div style={{ marginTop: 18 }} />

        <div className="setup-steps">
          {steps.map((step, i) => (
            <SetupStep key={step.title} index={i + 1} {...step} />
          ))}

          <SetupStep
            index={steps.length + 1}
            title="Ready"
            state={allReady ? "ok" : "pending"}
            statusLabel={allReady ? "System operational" : "Almost there"}
            explanation={
              allReady
                ? "Everything required is configured. Open Chat or Agents and ask an agent to do real work."
                : "Finish the required steps above to get a fully working local AI workforce."
            }
            action={
              allReady
                ? { label: "Open Chat", onClick: () => navigate("chat") }
                : undefined
            }
          />
        </div>
      </>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="🚀"
        title="Easy Start"
        subtitle="Get set up step by step — no terminal required."
        badge={<Badge tone="alpha">Onboarding</Badge>}
      />
      {renderBody()}
    </div>
  );
}

// ---- step derivation ------------------------------------------------------

type DerivedStep = Omit<SetupStepProps, "index"> & { required: boolean };

function buildSteps(
  s: SetupStatus,
  actions: { navigate: (v: "models" | "agents" | "knowledge" | "images" | "settings" | "chat") => void; openOllama: () => void },
): DerivedStep[] {
  const { navigate, openOllama } = actions;

  const modelState: StepState = s.ollama.recommended_available
    ? "ok"
    : s.models.count > 0
      ? "warn"
      : "warn";

  return [
    {
      title: "Backend",
      required: true,
      state: "ok",
      statusLabel: "Running",
      explanation: "The local Agent Engine is running and responding.",
      detail: `v${s.backend.version}`,
    },
    {
      title: "Ollama",
      required: true,
      state: s.ollama.reachable ? "ok" : "warn",
      statusLabel: s.ollama.reachable ? "Installed" : "Not running",
      explanation: s.ollama.reachable
        ? "Ollama (the local AI runtime) is installed and reachable."
        : "Install Ollama and make sure it's running. It powers your agents locally and for free.",
      detail: s.ollama.reachable && s.ollama.version ? `Ollama ${s.ollama.version}` : undefined,
      action: s.ollama.reachable ? undefined : { label: "Get Ollama", onClick: openOllama },
    },
    {
      title: "Recommended Model",
      required: true,
      state: s.models.count > 0 ? "ok" : modelState,
      statusLabel:
        s.models.count > 0
          ? s.ollama.recommended_available
            ? `${s.ollama.recommended_model} installed`
            : `${s.models.count} model(s) installed`
          : "No models",
      explanation:
        s.models.count > 0
          ? "At least one local model is installed. Agents will use it to think."
          : "Install a model so your agents have a brain. The recommended one is a good start.",
      detail: s.models.installed.length > 0 ? s.models.installed.join(", ") : undefined,
      action: { label: "Manage models", onClick: () => navigate("models") },
    },
    {
      title: "SQLite",
      required: true,
      state: s.sqlite.connected ? "ok" : "error",
      statusLabel: s.sqlite.connected ? "Ready" : "Not initialized",
      explanation: s.sqlite.connected
        ? "The local database stores your agents, documents, routines, and logs."
        : "The local database isn't initialized. Restart the backend.",
      detail: s.sqlite.connected ? `${s.sqlite.table_count} tables` : undefined,
    },
    {
      title: "Workspace Folder",
      required: true,
      state: s.workspace.ready && s.workspace.configured ? "ok" : "warn",
      statusLabel: s.workspace.ready && s.workspace.configured ? "Configured" : "Not configured",
      explanation:
        s.workspace.ready && s.workspace.configured
          ? "Your workspace is set up. It's the only place agents can read and write files."
          : "Choose a workspace folder. Agents' file tools are confined to it for safety.",
      detail: s.workspace.path,
      action: { label: "Configure workspace", onClick: () => navigate("settings") },
    },
    {
      title: "Tool Permissions",
      required: true,
      state: s.agents.with_tools > 0 ? "ok" : "warn",
      statusLabel: s.agents.with_tools > 0 ? "Granted" : "None granted",
      explanation:
        s.agents.with_tools > 0
          ? "At least one agent can use tools to take real local actions."
          : "Enable tools for an agent so it can create folders, write files, and more. Tools are deny-by-default.",
      detail:
        s.agents.count > 0
          ? `${s.agents.with_tools}/${s.agents.count} agents have tools enabled`
          : "No agents yet",
      action: { label: "Open Agents", onClick: () => navigate("agents") },
    },
    {
      title: "Knowledge Base",
      required: false,
      state: s.chromadb.available ? "ok" : "warn",
      statusLabel: s.chromadb.available ? "Ready" : "Not ready",
      explanation: s.chromadb.available
        ? "The local knowledge base is available for retrieval-augmented answers (RAG)."
        : "Import documents to give agents private context. First import downloads a small embedding model.",
      detail: s.chromadb.available ? `${s.chromadb.document_count} documents indexed` : undefined,
      action: { label: "Open Knowledge Base", onClick: () => navigate("knowledge") },
    },
    {
      title: "ComfyUI (optional)",
      required: false,
      state: s.comfyui.enabled && s.comfyui.reachable ? "ok" : "optional",
      statusLabel:
        s.comfyui.enabled && s.comfyui.reachable
          ? "Connected"
          : s.comfyui.enabled
            ? "Not reachable"
            : "Optional",
      explanation:
        s.comfyui.enabled && s.comfyui.reachable
          ? "Local image generation via ComfyUI is connected."
          : "Optional. Connect a local ComfyUI instance if you want agents to generate images.",
      action: { label: "Image settings", onClick: () => navigate("images") },
    },
  ];
}
