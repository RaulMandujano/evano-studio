import { PageHeader } from "../components/ui/PageHeader";
import { StatusCard, type StatusCardProps } from "../components/ui/StatusCard";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { AgentEngineStatusCard } from "../components/dashboard/AgentEngineStatusCard";
import { OllamaStatusCard } from "../components/dashboard/OllamaStatusCard";
import { useAppInfo } from "../hooks/useAppInfo";
import { useAgentEngineStatus } from "../hooks/useAgentEngineStatus";
import { useOllamaStatus } from "../hooks/useOllama";

/**
 * Secondary status tiles. These are READ-ONLY and reflect the honest current
 * state: nothing is connected or initialized yet. They stay static for now and
 * will become live as each integration is added. (The Agent Engine and Ollama
 * cards above the grid are live.)
 */
const statusCards: StatusCardProps[] = [
  {
    icon: "🧠",
    title: "Default model",
    status: "Gemma 4",
    tone: "info",
    hint: "Recommended local model when available.",
  },
  {
    icon: "🗄️",
    title: "SQLite database",
    status: "Not initialized",
    tone: "pending",
    hint: "Stores agents, routines, and history locally.",
  },
  {
    icon: "📚",
    title: "ChromaDB local",
    status: "Not checked",
    tone: "pending",
    hint: "Local knowledge base / RAG. No cloud.",
  },
  {
    icon: "🎨",
    title: "ComfyUI local",
    status: "Not checked",
    tone: "pending",
    hint: "Optional, user-run local image generation.",
  },
  {
    icon: "🔁",
    title: "Routines",
    status: "Not configured",
    tone: "neutral",
    hint: "Scheduled agent tasks.",
  },
  {
    icon: "🗓️",
    title: "Calendar",
    status: "Ready",
    tone: "ok",
    hint: "Visual view for routines.",
  },
  {
    icon: "🆓",
    title: "Free by default",
    status: "Enabled",
    tone: "ok",
    hint: "No paid APIs, no cloud lock-in.",
  },
];

export function DashboardView() {
  const info = useAppInfo();
  const engine = useAgentEngineStatus();
  const ollama = useOllamaStatus();

  return (
    <div className="view">
      <PageHeader
        icon="🏠"
        title="Dashboard"
        subtitle="A quick look at your local Evano Studio setup. The Agent Engine card below is live; the rest become live as each integration is added."
        badge={<Badge tone="alpha">Alpha</Badge>}
      />

      <AgentEngineStatusCard {...engine} />
      <OllamaStatusCard {...ollama} />

      <section className="status-grid">
        {statusCards.map((card) => (
          <StatusCard key={card.title} {...card} />
        ))}
      </section>

      <Card className="env-card">
        <div className="env-card-head">
          <h3>Environment</h3>
          <Badge tone="ok" dot>
            Local only
          </Badge>
        </div>
        {info ? (
          <dl className="env-grid">
            <div>
              <dt>App</dt>
              <dd>
                {info.name} v{info.version}
              </dd>
            </div>
            <div>
              <dt>Platform</dt>
              <dd>{info.platform}</dd>
            </div>
            <div>
              <dt>Electron</dt>
              <dd>{info.versions.electron}</dd>
            </div>
            <div>
              <dt>Chromium</dt>
              <dd>{info.versions.chrome}</dd>
            </div>
            <div>
              <dt>Node</dt>
              <dd>{info.versions.node}</dd>
            </div>
          </dl>
        ) : (
          <p className="muted">Reading runtime info…</p>
        )}
        <p className="env-note">
          Runtime details are read over the secure preload bridge — a small, safe
          example of the IPC pattern future features will use.
        </p>
      </Card>
    </div>
  );
}
