import { useEffect, useState } from "react";
import { Card } from "../ui/Card";
import { Badge, type BadgeTone } from "../ui/Badge";
import { Button } from "../ui/Button";
import { backendApi } from "../../lib/api/client";
import type { Agent, DiscordStatus } from "../../lib/api/types";

const STATE_TONE: Record<string, BadgeTone> = {
  running: "ok",
  starting: "pending",
  error: "danger",
  disabled: "neutral",
  stopped: "neutral",
};

/**
 * Opt-in Discord channel. Connects a Discord bot to one agent. The agent's tools
 * stay workspace-confined and permission-gated — Discord grants no extra power.
 * Replies only to the allowed Discord user IDs (deny-by-default).
 */
export function DiscordSettings() {
  const [status, setStatus] = useState<DiscordStatus | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [enabled, setEnabled] = useState(false);
  const [token, setToken] = useState("");
  const [agentId, setAgentId] = useState<string>("");
  const [allowed, setAllowed] = useState("");
  const [saving, setSaving] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const load = async () => {
    try {
      const [s, a, settings] = await Promise.all([
        backendApi.getDiscordStatus(),
        backendApi.getAgents(),
        backendApi.getSettings(),
      ]);
      setStatus(s);
      setAgents(a);
      setEnabled((settings.settings.discord_enabled ?? "").toLowerCase() === "true");
      setToken(settings.settings.discord_bot_token ?? "");
      setAgentId(settings.settings.discord_agent_id ?? (s.agent_id ? String(s.agent_id) : ""));
      setAllowed(settings.settings.discord_allowed_user_ids ?? "");
    } catch {
      /* backend offline; leave defaults */
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const save = async () => {
    setSaving(true);
    setNote(null);
    try {
      await backendApi.updateSettings({
        discord_enabled: enabled ? "true" : "false",
        discord_bot_token: token.trim(),
        discord_agent_id: agentId,
        discord_allowed_user_ids: allowed.trim(),
      });
      setNote("Saved. Restart the backend to connect (or disconnect) Discord.");
      await load();
    } catch (e) {
      setNote(e instanceof Error ? e.message : "Couldn't save Discord settings.");
    } finally {
      setSaving(false);
    }
  };

  if (status && !status.available) {
    return (
      <Card className="card-spaced">
        <h3 className="settings-section-title">Discord channel</h3>
        <p className="muted">
          The Discord library isn&apos;t installed in the backend. Install it with{" "}
          <span className="mono">pip install discord.py</span> and restart.
        </p>
      </Card>
    );
  }

  return (
    <Card className="card-spaced">
      <div className="env-card-head">
        <h3 className="settings-section-title">Discord channel</h3>
        {status ? (
          <Badge tone={STATE_TONE[status.state] ?? "neutral"} dot>
            {status.state}
          </Badge>
        ) : null}
      </div>
      <p className="muted form-hint">
        Talk to one of your agents from Discord. The agent stays workspace-confined; it only
        replies to the Discord user IDs you allow.
      </p>

      <div className="form-row">
        <label>
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />{" "}
          Enable Discord
        </label>
      </div>

      <div className="form-row">
        <label htmlFor="dc-token">Bot token</label>
        <input
          id="dc-token"
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Discord bot token (from the Developer Portal)"
        />
      </div>

      <div className="form-row">
        <label htmlFor="dc-agent">Agent</label>
        <select
          id="dc-agent"
          className="select"
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
        >
          <option value="">Select an agent…</option>
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name} ({a.model_name})
            </option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <label htmlFor="dc-allowed">Allowed Discord user IDs</label>
        <input
          id="dc-allowed"
          value={allowed}
          onChange={(e) => setAllowed(e.target.value)}
          placeholder="e.g. 123456789012345678, 987654321098765432"
        />
        <p className="form-hint">
          Comma-separated. Only these users get replies. Enable Developer Mode in Discord, then
          right-click a user → Copy User ID. Also enable “Message Content Intent” for your bot.
        </p>
      </div>

      <div className="form-actions">
        <Button variant="primary" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save Discord settings"}
        </Button>
      </div>

      {note ? <p className="settings-ok">{note}</p> : null}
      {status?.message ? <p className="form-hint">{status.message}</p> : null}
    </Card>
  );
}
