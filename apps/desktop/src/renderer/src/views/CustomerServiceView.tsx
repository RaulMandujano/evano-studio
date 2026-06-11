/**
 * Customer Service — your AI support desk, mostly for WhatsApp.
 *
 * Guided setup in four steps: pick (or create) the support agent, teach it the
 * business (knowledge base), connect a customer channel (WhatsApp pairs with a
 * QR from the dashboard; Telegram/Discord/Slack take a bot token), and route
 * the channel to the agent. From then on, every customer message is answered
 * by an agent that knows your business — each customer gets its own memory.
 */
import { useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";
import type { CustomerServiceStatus, KnowledgeStatus } from "../lib/api/types";

const SUPPORT_AGENT_TEMPLATE = {
  name: "Customer Support",
  emoji: "🎧",
  instructions: [
    "You are this business's customer service agent. Answer customer messages quickly, warmly, and concisely.",
    "- ALWAYS search your memory first — the business knowledge (hours, prices, policies, FAQs) lives there.",
    "- Never invent prices, policies, or promises. If the answer isn't in your knowledge, say so politely.",
    "- If the customer is upset or asks for a human, apologize, say you'll escalate, and ask them to wait.",
    "- Reply in the customer's language.",
  ].join("\n"),
};

export function CustomerServiceView() {
  const navigate = useNavigate();
  const res = useBackendResource<CustomerServiceStatus>(backendApi.getCustomerServiceStatus, "cs-status");
  const kbRes = useBackendResource<KnowledgeStatus>(backendApi.getKnowledgeStatus, "kb-status");

  const [agentId, setAgentId] = useState("");
  const [channel, setChannel] = useState("whatsapp");
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [noteOk, setNoteOk] = useState(false);

  const status = res.data;
  const kbDocs = kbRes.data?.document_count ?? 0;
  const live = !!status?.ok && status.assignments.length > 0 && status.gateway_running;

  const say = (ok: boolean, message: string) => {
    setNoteOk(ok);
    setNote(message);
  };

  const createSupportAgent = async () => {
    setBusy("create");
    setNote(null);
    try {
      const r = await backendApi.createOpenClawAgent(SUPPORT_AGENT_TEMPLATE);
      say(r.ok, r.ok ? `Agent “${r.agent?.name}” created — it already knows how to behave with customers.` : r.message);
      if (r.ok) {
        if (r.agent) setAgentId(r.agent.id);
        res.refresh();
      }
    } catch (e) {
      say(false, e instanceof Error ? e.message : "Couldn't create the agent.");
    } finally {
      setBusy(null);
    }
  };

  const activate = async () => {
    if (!agentId || !channel) return;
    setBusy("assign");
    setNote(null);
    try {
      const r = await backendApi.assignSupportAgent(agentId, channel);
      say(r.ok, r.message);
      if (r.ok) res.refresh();
    } catch (e) {
      say(false, e instanceof Error ? e.message : "Couldn't activate the routing.");
    } finally {
      setBusy(null);
    }
  };

  const deactivate = async (aId: string, ch: string) => {
    if (!window.confirm(`Stop routing ${ch} messages to this agent?`)) return;
    setBusy("unassign");
    setNote(null);
    try {
      const r = await backendApi.unassignSupportAgent(aId, ch);
      say(r.ok, r.message);
      if (r.ok) res.refresh();
    } catch (e) {
      say(false, e instanceof Error ? e.message : "Couldn't remove the routing.");
    } finally {
      setBusy(null);
    }
  };

  const startGateway = async () => {
    setBusy("gateway");
    try {
      const r = await backendApi.startOpenClawGateway();
      say(r.ok, r.running ? "Gateway running — your support agent is online." : r.message);
      res.refresh();
    } catch (e) {
      say(false, e instanceof Error ? e.message : "Couldn't start the gateway.");
    } finally {
      setBusy(null);
    }
  };

  if (res.state === "ready" && status && !status.ok) {
    return (
      <div className="view">
        <PageHeader icon="🎧" title="Customer Service" subtitle="Your AI support desk." />
        <Card className="notice-card">
          <h3>OpenClaw isn&apos;t ready yet</h3>
          <p className="muted">{status.message || "Finish the setup first."}</p>
          <div className="form-actions"><Button variant="primary" onClick={() => navigate("openclaw")}>Go to setup</Button></div>
        </Card>
      </div>
    );
  }

  const agentName = (id: string) => {
    const a = status?.agents.find((x) => x.id === id);
    return a ? `${a.emoji ? a.emoji + " " : ""}${a.name}` : id;
  };
  const channelMeta = (slug: string) => status?.channels.find((c) => c.slug === slug);

  return (
    <div className="view">
      <PageHeader
        icon="🎧"
        title="Customer Service"
        subtitle="An agent that answers your customers — on WhatsApp and beyond — using your business knowledge."
      />

      {live ? (
        <div className="cs-live">
          <span className="cs-live-dot" aria-hidden="true" />
          <strong>Customer service is LIVE.</strong>
          <span className="muted">
            {status!.assignments.map((a) => `${channelMeta(a.channel)?.icon ?? "💬"} ${channelMeta(a.channel)?.name ?? a.channel} → ${agentName(a.agent_id)}`).join(" · ")}
          </span>
        </div>
      ) : null}

      {note ? <p className={noteOk ? "settings-ok" : "form-error"}>{note}</p> : null}
      {res.state === "checking" ? <p className="muted">Checking your setup…</p> : null}

      {status?.ok ? (
        <div className="cs-steps">
          {/* 1 — the support agent */}
          <Card className="cs-step">
            <div className="cs-step-head">
              <span className="cs-step-num">1</span>
              <h3>Your support agent</h3>
              {status.agents.length > 0 ? <Badge tone="ok" dot>{status.agents.length} available</Badge> : null}
            </div>
            <p className="muted">
              The agent that will talk to customers. Create a ready-made one (friendly tone, sticks to
              your business facts, escalates to a human when unsure) or use an existing agent.
            </p>
            <div className="form-actions">
              <Button variant="primary" onClick={createSupportAgent} disabled={busy !== null}>
                {busy === "create" ? "Creating…" : "🎧 Create support agent"}
              </Button>
              <Button variant="ghost" onClick={() => navigate("openclaw-agents")}>Manage agents</Button>
            </div>
          </Card>

          {/* 2 — knowledge */}
          <Card className="cs-step">
            <div className="cs-step-head">
              <span className="cs-step-num">2</span>
              <h3>Teach it your business</h3>
              {kbDocs > 0 ? (
                <Badge tone="ok" dot>{kbDocs} document(s)</Badge>
              ) : (
                <Badge tone="pending" dot>Nothing imported yet</Badge>
              )}
            </div>
            <p className="muted">
              Import your prices, hours, policies, and FAQs into the Knowledge Base — it syncs into the
              agent&apos;s memory automatically, so it answers with YOUR facts (even on WhatsApp).
            </p>
            <div className="form-actions">
              <Button onClick={() => navigate("knowledge")}>📚 Open Knowledge Base</Button>
            </div>
          </Card>

          {/* 3 — channel */}
          <Card className="cs-step">
            <div className="cs-step-head">
              <span className="cs-step-num">3</span>
              <h3>Connect a customer channel</h3>
            </div>
            <div className="cs-channels">
              {status.channels.map((c) => (
                <div key={c.slug} className={`cs-channel ${c.configured ? "is-on" : ""}`}>
                  <span className="cs-channel-icon">{c.icon}</span>
                  <span className="cs-channel-name">{c.name}</span>
                  {c.configured ? (
                    <Badge tone="ok" dot>Connected</Badge>
                  ) : c.connect === "login" ? (
                    <Button onClick={() => navigate("openclaw-dashboard")}>Scan QR in Dashboard</Button>
                  ) : (
                    <Button onClick={() => navigate("channels")}>Connect with token</Button>
                  )}
                </div>
              ))}
            </div>
            <p className="form-hint">
              WhatsApp pairs by scanning a QR (like WhatsApp Web) from the Dashboard. Telegram, Discord,
              and Slack connect with a bot token from the Channels page.
            </p>
          </Card>

          {/* 4 — activate */}
          <Card className="cs-step">
            <div className="cs-step-head">
              <span className="cs-step-num">4</span>
              <h3>Turn it on</h3>
            </div>
            <p className="muted">
              Route the channel&apos;s incoming messages to your support agent. Each customer gets their
              own conversation memory.
            </p>
            <div className="cs-activate">
              <select value={agentId} onChange={(e) => setAgentId(e.target.value)} disabled={busy !== null}>
                <option value="">— choose the agent —</option>
                {status.agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.emoji ? `${a.emoji} ` : ""}{a.name}</option>
                ))}
              </select>
              <span className="muted">answers</span>
              <select value={channel} onChange={(e) => setChannel(e.target.value)} disabled={busy !== null}>
                {status.channels.map((c) => (
                  <option key={c.slug} value={c.slug}>{c.icon} {c.name}{c.configured ? "" : " (not connected)"}</option>
                ))}
              </select>
              <Button variant="primary" onClick={activate} disabled={busy !== null || !agentId}>
                {busy === "assign" ? "Activating…" : "✨ Activate"}
              </Button>
            </div>

            {status.assignments.length > 0 ? (
              <ul className="cs-assignments">
                {status.assignments.map((a) => (
                  <li key={`${a.channel}-${a.agent_id}`} className="cs-assignment">
                    <span>
                      {channelMeta(a.channel)?.icon ?? "💬"} {channelMeta(a.channel)?.name ?? a.channel} →{" "}
                      <strong>{agentName(a.agent_id)}</strong>
                    </span>
                    <Button variant="ghost" onClick={() => deactivate(a.agent_id, a.channel)} disabled={busy !== null}>
                      Stop
                    </Button>
                  </li>
                ))}
              </ul>
            ) : null}

            {!status.gateway_running ? (
              <p className="form-hint">
                ⚠️ The gateway isn&apos;t running — messages won&apos;t be answered until it is.{" "}
                <Button variant="primary" onClick={startGateway} disabled={busy !== null}>
                  {busy === "gateway" ? "Starting…" : "Start the gateway"}
                </Button>
              </p>
            ) : null}
          </Card>
        </div>
      ) : null}
    </div>
  );
}
