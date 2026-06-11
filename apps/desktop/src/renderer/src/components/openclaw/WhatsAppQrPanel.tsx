/**
 * In-app WhatsApp pairing — the live QR, right here, like WhatsApp Web.
 *
 * Starts the pairing on mount, polls while open, renders the QR inline, and
 * cancels the attempt when closed without scanning.
 */
import { useEffect, useRef, useState } from "react";
import { Button } from "../ui/Button";
import { backendApi } from "../../lib/api/client";
import type { WhatsAppLoginStatus } from "../../lib/api/types";

export function WhatsAppQrPanel({ onConnected, onClose }: { onConnected: () => void; onClose: () => void }) {
  const [status, setStatus] = useState<WhatsAppLoginStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const connectedNotified = useRef(false);

  useEffect(() => {
    let stopped = false;
    let timer: number | undefined;

    const poll = async (): Promise<void> => {
      try {
        const s = await backendApi.getWhatsAppLoginStatus();
        if (stopped) return;
        setStatus(s);
        if (s.state === "connected" && !connectedNotified.current) {
          connectedNotified.current = true;
          onConnected();
          return; // stop polling — we're done
        }
      } catch (e) {
        if (!stopped) setError(e instanceof Error ? e.message : "Lost contact with the engine.");
      }
      if (!stopped) timer = window.setTimeout(() => void poll(), 1500);
    };

    void backendApi
      .startWhatsAppLogin()
      .then((s) => {
        if (!stopped) setStatus(s);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Couldn't start the pairing."))
      .finally(() => void poll());

    return () => {
      stopped = true;
      if (timer !== undefined) window.clearTimeout(timer);
      // Closing without finishing → stop the background login attempt.
      if (!connectedNotified.current) void backendApi.cancelWhatsAppLogin().catch(() => undefined);
    };
  }, [onConnected]);

  const retry = async () => {
    setError(null);
    connectedNotified.current = false;
    try {
      setStatus(await backendApi.startWhatsAppLogin());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't restart the pairing.");
    }
  };

  const state = status?.state ?? "starting";

  return (
    <div className="wa-qr">
      <div className="wa-qr-head">
        <h4>📱 Link WhatsApp</h4>
        <Button variant="ghost" onClick={onClose}>Close</Button>
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      {state === "starting" || (state === "idle" && !error) ? (
        <p className="muted">Generating your QR code…</p>
      ) : null}

      {state === "qr" && status?.qr_svg ? (
        <>
          <div className="wa-qr-code" dangerouslySetInnerHTML={{ __html: status.qr_svg }} />
          <ol className="wa-qr-steps muted">
            <li>Open WhatsApp on your phone</li>
            <li>Settings → <strong>Linked devices</strong> → <strong>Link a device</strong></li>
            <li>Scan this code (it refreshes by itself)</li>
          </ol>
        </>
      ) : null}

      {state === "connected" ? (
        <p className="settings-ok">✅ WhatsApp linked! Your agent can now answer customers there.</p>
      ) : null}

      {state === "error" || state === "expired" ? (
        <>
          <p className="form-error">
            {state === "expired" ? "The QR expired — generate a fresh one." : status?.message || "Pairing failed."}
          </p>
          <div className="form-actions">
            <Button variant="primary" onClick={retry}>Try again</Button>
          </div>
        </>
      ) : null}
    </div>
  );
}
