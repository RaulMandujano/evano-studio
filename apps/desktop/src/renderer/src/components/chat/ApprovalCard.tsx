import { useState } from "react";
import { Button } from "../ui/Button";
import { backendApi } from "../../lib/api/client";
import type { ActionResolveResponse, PendingAction } from "../../lib/api/types";

interface ApprovalCardProps {
  action: PendingAction;
  /** Called with the outcome so the chat can show what happened. */
  onResolved: (outcome: { approved: boolean; result: ActionResolveResponse | null; error?: string }) => void;
}

/**
 * Human-in-the-loop approval: the agent proposed a sensitive computer action and
 * it will NOT run until the user clicks Allow. Shows the exact app/URL/command.
 */
export function ApprovalCard({ action, onResolved }: ApprovalCardProps) {
  const [busy, setBusy] = useState<"approve" | "deny" | null>(null);

  const resolve = async (approve: boolean) => {
    setBusy(approve ? "approve" : "deny");
    try {
      const result = approve
        ? await backendApi.approveAction(action.id)
        : await backendApi.denyAction(action.id);
      onResolved({ approved: approve, result });
    } catch (e) {
      onResolved({ approved: approve, result: null, error: e instanceof Error ? e.message : "Failed." });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="approval-card">
      <div className="approval-head">
        <span aria-hidden="true">🔐</span>
        <span>
          The agent wants to <strong>{action.summary}</strong>. Allow it?
        </span>
      </div>
      <pre className="approval-preview mono">{action.preview}</pre>
      <div className="approval-actions">
        <Button variant="primary" onClick={() => resolve(true)} disabled={busy !== null}>
          {busy === "approve" ? "Running…" : "Allow / Permitir"}
        </Button>
        <Button onClick={() => resolve(false)} disabled={busy !== null}>
          {busy === "deny" ? "…" : "Deny / Rechazar"}
        </Button>
      </div>
    </div>
  );
}
