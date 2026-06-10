/** tools endpoints. */
import { requestJson } from "../http";
import type {
  ToolSpec,
  ToolTestResponse,
  ToolExecutionLog,
  ActionResolveResponse,
} from "../types";


/** `GET /tools` — list available tools. */
export function getTools(): Promise<ToolSpec[]> {
  return requestJson<ToolSpec[]>("/tools");
}

/** `POST /tools/test` — run a tool with params (optionally as an agent). */
export function testTool(
  toolId: string,
  params: Record<string, unknown>,
  agentId?: number,
): Promise<ToolTestResponse> {
  return requestJson<ToolTestResponse>("/tools/test", {
    method: "POST",
    body: { tool_id: toolId, params, agent_id: agentId ?? null },
    timeoutMs: 60_000,
  });
}

/** `GET /tools/logs` — recent tool executions (newest first). */
export function getToolLogs(limit = 50): Promise<ToolExecutionLog[]> {
  return requestJson<ToolExecutionLog[]>(`/tools/logs?limit=${limit}`);
}

/** `POST /actions/{id}/approve` — approve & run a proposed computer action. */
export function approveAction(id: number): Promise<ActionResolveResponse> {
  return requestJson<ActionResolveResponse>(`/actions/${id}/approve`, {
    method: "POST",
    timeoutMs: 120_000,
  });
}

/** `POST /actions/{id}/deny` — deny a proposed computer action. */
export function denyAction(id: number): Promise<ActionResolveResponse> {
  return requestJson<ActionResolveResponse>(`/actions/${id}/deny`, { method: "POST" });
}

