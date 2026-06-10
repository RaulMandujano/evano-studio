/**
 * Connect ONE agent to Discord as its own bot — written for non-technical users.
 *
 * The only manual part is creating the bot in Discord's Developer Portal (no API
 * can do that for the user); everything after pasting the token is one click:
 * Evano registers the token as the agent's own channel account, binds it, and
 * reloads the gateway. Add several agents to one server and you get a remote
 * "workspace" where the whole team is reachable.
 */
import { useCallback, useState } from "react";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { backendApi } from "../../lib/api/client";
import { useBackendResource } from "../../hooks/useBackendResource";
import type { OpenClawAgent } from "../../lib/api/types";

const PORTAL_URL = "https://discord.com/developers/applications";

const STEPS: { title: string; desc: string }[] = [
  {
    title: "Create the bot",
    desc: 'Open the Discord Developer Portal (button below), click "New Application", and name it after your agent.',
  },
  {
    title: "Copy the token",
    desc: 'In the left menu open "Bot", click "Reset Token", and copy it. On that same page, turn ON "Message Content Intent" (under Privileged Gateway Intents) — without it the bot can\'t read messages.',
  },
  {
    title: "Invite it to your server",
    desc: 'Open "OAuth2" → "URL Generator", tick "bot", tick "Send Messages" and "Read Message History", then open the generated link and pick your server.',
  },
  {
    title: "Paste the token below",
    desc: "Evano does the rest — it links the bot to this agent and brings it online.",
  },
];

export function AgentDiscordPanel({ agent, onBack }: { agent: OpenClawAgent; onBack: () => void }) {
  const fetchStatus = useCallback(() => backendApi.getAgentDiscordStatus(agent.id), [agent.id]);
  const status = useBackendResource(fetchStatus);

  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [noteOk, setNoteOk] = useState(false);

  const connected = status.data?.ok === true && status.data.connected;
  const gatewayRunning = status.data?.gateway_running === true;

  const connect = async () => {
    setBusy(true);
    setNote(null);
    try {
      const r = await backendApi.connectAgentDiscord(agent.id, token);
      setNoteOk(r.ok);
      setNote(r.message);
      if (r.ok) {
        setToken("");
        status.refresh();
      }
    } catch (e) {
      setNoteOk(false);
      setNote(e instanceof Error ? e.message : "Couldn't connect the bot.");
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async () => {
    if (!window.confirm(`Disconnect “${agent.name || agent.id}” from Discord?`)) return;
    setBusy(true);
    setNote(null);
    try {
      const r = await backendApi.disconnectAgentDiscord(agent.id);
      setNoteOk(r.ok);
      setNote(r.message);
      if (r.ok) status.refresh();
    } catch (e) {
      setNoteOk(false);
      setNote(e instanceof Error ? e.message : "Couldn't disconnect.");
    } finally {
      setBusy(false);
    }
  };

  const startGateway = async () => {
    setBusy(true);
    setNote(null);
    try {
      const r = await backendApi.startOpenClawGateway();
      setNoteOk(r.ok);
      setNote(r.running ? "Gateway running — your bot is online." : r.message || "Couldn't start the gateway.");
      status.refresh();
    } catch (e) {
      setNoteOk(false);
      setNote(e instanceof Error ? e.message : "Couldn't start the gateway.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="view">
      <div className="agent-detail-head">
        <div>
          <h3>💬 {agent.name || agent.id} on Discord</h3>
          <p className="muted">
            Make this agent its own Discord bot — talk to it from your phone, or put your whole
            team in one server.
          </p>
        </div>
        <div className="agent-detail-actions">
          {status.state === "ready" && status.data?.ok ? (
            connected ? <Badge tone="ok" dot>Connected</Badge> : <Badge tone="neutral" dot>Not connected</Badge>
          ) : null}
          <Button onClick={onBack}>← Back</Button>
        </div>
      </div>

      {status.state === "checking" ? <p className="muted">Checking this agent&apos;s Discord link…</p> : null}

      {connected ? (
        <Card className="card-spaced">
          <h3 className="settings-section-title">✅ This agent is a Discord bot</h3>
          <p className="muted">
            Mention it or message it in your server and it will answer as{" "}
            <strong>{agent.name || agent.id}</strong>.
          </p>
          {!gatewayRunning ? (
            <>
              <p className="form-hint">
                ⚠️ The OpenClaw gateway isn&apos;t running, so the bot is offline right now.
              </p>
              <div className="form-actions">
                <Button variant="primary" onClick={startGateway} disabled={busy}>
                  {busy ? "Starting…" : "Start the gateway"}
                </Button>
              </div>
            </>
          ) : null}
          <div className="form-actions">
            <Button onClick={disconnect} disabled={busy}>Disconnect from Discord</Button>
          </div>
        </Card>
      ) : (
        <Card className="card-spaced">
          <h3 className="settings-section-title">Set it up once — about 3 minutes</h3>
          <ol className="dsc-steps">
            {STEPS.map((s, i) => (
              <li key={s.title} className="dsc-step">
                <span className="dsc-step-num">{i + 1}</span>
                <div className="dsc-step-body">
                  <p className="dsc-step-title">{s.title}</p>
                  <p className="dsc-step-desc muted">{s.desc}</p>
                  {i === 0 ? (
                    <div className="form-actions">
                      <Button onClick={() => void window.evano?.services?.openExternal?.(PORTAL_URL)}>
                        Open Discord Developer Portal ↗
                      </Button>
                    </div>
                  ) : null}
                </div>
              </li>
            ))}
          </ol>

          <div className="form-row">
            <label htmlFor="dsc-token">Discord bot token</label>
            <input
              id="dsc-token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste the bot token here…"
              autoComplete="off"
            />
            <p className="form-hint">Stored only on this computer, inside OpenClaw&apos;s config. Never logged.</p>
          </div>
          <div className="form-actions">
            <Button variant="primary" onClick={connect} disabled={busy || !token.trim()}>
              {busy ? "Connecting…" : "Connect to Discord"}
            </Button>
          </div>
        </Card>
      )}

      {note ? <p className={noteOk ? "settings-ok" : "form-error"}>{note}</p> : null}
    </div>
  );
}
