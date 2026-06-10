import { useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";
import type { ChannelsResponse, OpenClawChannel } from "../lib/api/types";

/** One channel card. Token-based channels connect inline; login-based ones
 *  (WhatsApp, Signal…) open the embedded dashboard to scan a QR / sign in. */
function ChannelCard({
  channel,
  onConnected,
  onOpenDashboard,
}: {
  channel: OpenClawChannel;
  onConnected: () => void;
  onOpenDashboard: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState(false);

  const connect = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const res = await backendApi.addOpenClawChannel({ channel: channel.slug, token });
      setErr(!res.ok);
      setMsg(res.message);
      if (res.ok) {
        setToken("");
        setOpen(false);
        onConnected();
      }
    } catch (e) {
      setErr(true);
      setMsg(e instanceof Error ? e.message : "Couldn't connect.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="channel-card">
      <div className="channel-head">
        <span className="channel-icon" aria-hidden="true">{channel.icon}</span>
        <span className="channel-name">{channel.name}</span>
        <Badge tone={channel.configured ? "ok" : "neutral"} dot>
          {channel.configured ? "Connected" : "Not connected"}
        </Badge>
      </div>

      {channel.connect === "login" || !channel.can_add ? (
        <>
          <p className="channel-hint muted">
            {channel.connect === "login"
              ? "Needs a quick sign-in (scan a QR or log in)."
              : "Set this one up from the dashboard."}
          </p>
          <Button onClick={onOpenDashboard}>
            {channel.configured ? "Manage in Dashboard" : "Connect in Dashboard"}
          </Button>
        </>
      ) : open ? (
        <div className="channel-form">
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder={`${channel.name} bot token`}
            autoFocus
          />
          <div className="form-actions">
            <Button variant="primary" onClick={connect} disabled={busy || !token.trim()}>
              {busy ? "Connecting…" : "Connect"}
            </Button>
            <Button onClick={() => { setOpen(false); setMsg(null); }} disabled={busy}>Cancel</Button>
          </div>
        </div>
      ) : (
        <Button onClick={() => setOpen(true)}>
          {channel.configured ? "Reconnect" : "Connect"}
        </Button>
      )}

      {msg ? <p className={err ? "form-error" : "settings-ok"}>{msg}</p> : null}
    </Card>
  );
}

/**
 * Channels — connect a messaging platform (WhatsApp, Discord, Telegram, Slack…)
 * so people can talk to your OpenClaw assistant from where they already chat.
 * All inside Evano: token-based channels connect with one paste; QR/login ones
 * open the embedded dashboard.
 */
export function ChannelsView() {
  const res = useBackendResource<ChannelsResponse>(backendApi.getOpenClawChannels);
  const navigate = useNavigate();
  const goDashboard = () => navigate("openclaw-dashboard");

  const renderBody = () => {
    if (res.state === "checking") return <p className="muted">Loading channels…</p>;
    if (res.state !== "ready" || !res.data) {
      return (
        <Card className="notice-card">
          <h3>Can&apos;t reach the engine</h3>
          <p className="muted">Evano&apos;s engine may still be starting — give it a moment, then retry.</p>
          <div className="form-actions"><Button variant="primary" onClick={res.refresh}>Retry</Button></div>
        </Card>
      );
    }
    if (!res.data.ok) {
      return (
        <Card className="notice-card">
          <h3>OpenClaw isn&apos;t ready yet</h3>
          <p className="muted">{res.data.message || "Finish the setup first, then connect your channels."}</p>
          <div className="form-actions"><Button variant="primary" onClick={() => navigate("openclaw")}>Go to setup</Button></div>
        </Card>
      );
    }

    const all = res.data.channels;
    const popular = all.filter((c) => c.popular);
    const rest = all.filter((c) => !c.popular);
    const connectedCount = all.filter((c) => c.configured).length;

    return (
      <>
        <Card className="setup-progress-card">
          <div className="setup-progress-head">
            <div>
              <h3 className="setup-progress-title">Connect a platform</h3>
              <p className="muted">
                Link WhatsApp, Discord, Telegram and more so people chat with your AI where they
                already are. {connectedCount > 0 ? `${connectedCount} connected.` : "None connected yet."}
              </p>
            </div>
            <Button onClick={res.refresh}>Refresh</Button>
          </div>
        </Card>

        <p className="section-label">Popular</p>
        <div className="channels-grid">
          {popular.map((c) => (
            <ChannelCard key={c.slug} channel={c} onConnected={res.refresh} onOpenDashboard={goDashboard} />
          ))}
        </div>

        {rest.length > 0 ? (
          <>
            <p className="section-label" style={{ marginTop: 18 }}>More platforms</p>
            <div className="channels-grid">
              {rest.map((c) => (
                <ChannelCard key={c.slug} channel={c} onConnected={res.refresh} onOpenDashboard={goDashboard} />
              ))}
            </div>
          </>
        ) : null}
      </>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="🔌"
        title="Channels"
        subtitle="Connect a messaging platform to talk to your OpenClaw assistant."
        badge={<Badge tone="alpha">Beta</Badge>}
      />
      {renderBody()}
    </div>
  );
}
