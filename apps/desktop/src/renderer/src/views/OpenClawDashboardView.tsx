import { createElement, useCallback, useEffect, useRef, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { backendApi } from "../lib/api/client";
import { useNavigate } from "../navigation-context";

/** Minimal shape of Electron's <webview> element we use. */
type WebviewEl = HTMLElement & {
  reload: () => void;
  loadURL: (url: string) => Promise<void>;
};

type Phase = "loading" | "ready" | "error";

/**
 * The OpenClaw control dashboard, embedded INSIDE Evano via an Electron
 * <webview>. The dashboard sends X-Frame-Options: DENY (so it can't be put in an
 * iframe); a <webview> is a separate top-level context, which is the safe way to
 * embed it. We pull a token-authenticated URL from the backend so it logs in
 * automatically — the client never copies a token or leaves the app.
 */
export function OpenClawDashboardView() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("loading");
  const [url, setUrl] = useState<string | null>(null);
  const [message, setMessage] = useState<string>("");
  const webviewRef = useRef<WebviewEl | null>(null);

  const load = useCallback(async () => {
    setPhase("loading");
    setMessage("");
    try {
      const res = await backendApi.getOpenClawDashboardUrl();
      if (res.ok && res.url) {
        setUrl(res.url);
        setPhase("ready");
      } else {
        setPhase("error");
        setMessage(res.message || "Couldn't get the dashboard URL.");
      }
    } catch (e) {
      setPhase("error");
      setMessage(e instanceof Error ? e.message : "Couldn't reach the engine.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const reload = () => {
    if (webviewRef.current) webviewRef.current.reload();
    else void load();
  };

  const openInBrowser = () => {
    if (url) void window.evano?.services?.openExternal?.(url);
  };

  const renderBody = () => {
    if (phase === "loading") {
      return (
        <Card className="notice-card">
          <h3>Opening the dashboard…</h3>
          <p className="muted">Starting OpenClaw and signing you in automatically.</p>
        </Card>
      );
    }
    if (phase === "error") {
      return (
        <Card className="notice-card">
          <h3>Can&apos;t open the dashboard yet</h3>
          <p className="muted">{message || "Make sure OpenClaw is set up and running."}</p>
          <div className="form-actions">
            <Button variant="primary" onClick={load}>Try again</Button>
            <Button onClick={() => navigate("openclaw")}>Go to setup</Button>
          </div>
        </Card>
      );
    }
    // ready — embed the dashboard
    return (
      <div className="oc-webview-frame">
        {url
          ? createElement("webview", {
              ref: webviewRef,
              src: url,
              partition: "persist:openclaw",
              className: "oc-webview",
            })
          : null}
      </div>
    );
  };

  return (
    <div className="view oc-dashboard-view">
      <PageHeader
        icon="🖥️"
        title="OpenClaw Dashboard"
        subtitle="Chat and manage everything right here — no need to leave Evano."
        badge={
          <div className="oc-dash-actions">
            <Badge tone={phase === "ready" ? "ok" : "neutral"} dot>
              {phase === "ready" ? "Connected" : phase === "loading" ? "Opening…" : "Offline"}
            </Badge>
            <Button onClick={reload} disabled={phase === "loading"}>Reload</Button>
            <Button onClick={openInBrowser} disabled={!url}>Open in browser</Button>
          </div>
        }
      />
      {renderBody()}
    </div>
  );
}
