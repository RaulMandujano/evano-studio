/**
 * Live agent activity (the Office view).
 *
 * Mirrors `services/agent-engine/app/schemas/activity.py`.
 */

export type ActivityKind = "chat" | "team" | "routine";
export type ActivityStatus = "working" | "done" | "error";

/** One unit of agent work — a chat turn, a team step, or a routine run. */
export interface AgentActivity {
  id: number;
  /** Namespaced id: `openclaw:<slug>` or `builtin:<db id>`. */
  agent_id: string;
  agent_name: string;
  kind: ActivityKind;
  task: string;
  status: ActivityStatus;
  started_at: string;
  finished_at: string | null;
  note: string;
}

/** Response from `GET /activity`. */
export interface ActivitySnapshot {
  active: AgentActivity[];
  recent: AgentActivity[];
  generated_at: string;
}
