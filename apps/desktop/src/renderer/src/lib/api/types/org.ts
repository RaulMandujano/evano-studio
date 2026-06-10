/**
 * Org chart — who manages whom. Mirrors `services/agent-engine/app/schemas/org.py`.
 */

export interface OrgAgent {
  id: string;
  name: string;
  emoji: string;
  model: string;
  workspace: string;
  is_default: boolean;
}

export interface OrgLinkItem {
  agent_id: string;
  /** Empty string → top level (no manager). */
  parent_agent_id: string;
}

/** Response from `GET /org/chart`. */
export interface OrgChartResponse {
  ok: boolean;
  message: string;
  agents: OrgAgent[];
  links: OrgLinkItem[];
}

/** Response from `PUT /org/chart`. */
export interface OrgActionResult {
  ok: boolean;
  message: string;
}
