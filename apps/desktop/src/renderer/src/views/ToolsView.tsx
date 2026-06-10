import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ToolsTester } from "../components/settings/ToolsTester";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import type { ToolExecutionLog, WorkspaceStatus } from "../lib/api/types";

/** Shows the active workspace path (where file tools actually write). */
function ActiveWorkspace() {
  const wsRes = useBackendResource<WorkspaceStatus>(backendApi.getWorkspaceStatus);
  const ws = wsRes.data;

  const open = () => {
    if (ws?.path) void window.evano?.services?.openWorkspacePath?.(ws.path);
  };

  return (
    <Card>
      <div className="setup-progress-head">
        <div>
          <h3 className="settings-section-title">Active workspace</h3>
          <p className="muted form-hint">
            File tools read and write only inside this folder.
          </p>
          <p className="form-hint">
            <span className="mono">{ws?.path ?? "—"}</span>{" "}
            {ws ? (
              <Badge tone={ws.ready ? "ok" : "pending"} dot>
                {ws.ready ? "Ready" : ws.is_default ? "Default" : "Incomplete"}
              </Badge>
            ) : null}
          </p>
        </div>
        <Button onClick={open} disabled={!ws?.path}>
          📁 Open folder
        </Button>
      </div>
    </Card>
  );
}

/** Recent tool executions — every action agents (or you) take is logged here. */
function ToolLogs() {
  const logsRes = useBackendResource<ToolExecutionLog[]>(backendApi.getToolLogs);
  const logs = logsRes.data ?? [];

  return (
    <Card className="card-spaced">
      <div className="setup-progress-head">
        <div>
          <h3 className="settings-section-title">Tool execution log</h3>
          <p className="muted form-hint">
            Every tool run is recorded for transparency — manual tests and agent actions alike.
          </p>
        </div>
        <Button onClick={logsRes.refresh}>Refresh</Button>
      </div>

      {logsRes.state === "checking" ? (
        <p className="muted">Loading…</p>
      ) : logsRes.state !== "ready" ? (
        <p className="muted">Couldn&apos;t load logs. Is the backend running?</p>
      ) : logs.length === 0 ? (
        <p className="muted">No tool executions yet. Run a tool above to see it here.</p>
      ) : (
        <ul className="tool-log-list">
          {logs.map((log) => (
            <li key={log.id} className="tool-log-row">
              <Badge tone={log.status === "success" ? "ok" : "danger"} dot>
                {log.status}
              </Badge>
              <div className="tool-log-main">
                <span className="tool-log-action">{log.action}</span>
                {log.detail ? <span className="tool-log-detail mono"> · {log.detail}</span> : null}
                <span className="tool-log-meta muted">
                  {log.tool_name} · {log.source === "agent" ? log.agent_name ?? "agent" : "manual"} ·{" "}
                  {new Date(log.created_at).toLocaleString()}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

/** Tools page — manually test any tool and review the execution log. */
export function ToolsView() {
  return (
    <div className="view">
      <PageHeader
        icon="🛠️"
        title="Tools"
        subtitle="Test the safe, local tools your agents can use — all confined to the workspace."
        badge={<Badge tone="alpha">Live</Badge>}
      />
      <ActiveWorkspace />
      <div style={{ marginTop: 18 }} />
      <ToolsTester />
      <ToolLogs />
    </div>
  );
}
