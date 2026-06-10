/**
 * Agent tools (deny-by-default local actions).
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- Tools ----------------------------------------------------------------

export interface ToolParam {
  name: string;
  type: "string" | "text" | "integer";
  required: boolean;
  description: string;
}

/** A tool spec (from `GET /tools`). */
export interface ToolSpec {
  id: string;
  name: string;
  description: string;
  category: string;
  parameters: ToolParam[];
  requires_approval?: boolean;
}

/** Response from `POST /tools/test`. */
export interface ToolTestResponse {
  ok: boolean;
  result: unknown;
  message: string | null;
}

/** A logged tool execution (from `GET /tools/logs`). */
export interface ToolExecutionLog {
  id: number;
  agent_id: number | null;
  agent_name: string | null;
  tool_id: string;
  tool_name: string;
  source: string; // "manual" | "agent"
  action: string;
  status: string; // "success" | "error"
  detail: string | null;
  created_at: string;
}

