/**
 * AFM — Agent File Management. Mirrors `services/agent-engine/app/schemas/afm.py`.
 */

export interface AfmAgent {
  agent_id: string;
  name: string;
  emoji: string;
  workspace: string;
  target: string;
  managed: boolean;
}

export interface AfmTeam {
  team_id: number | null;
  name: string;
  folder: string;
  exists: boolean;
  members: string[];
}

/** Response from `GET /afm/status`. */
export interface AfmStatus {
  ok: boolean;
  message: string;
  root: string;
  is_default: boolean;
  configured: boolean;
  agents: AfmAgent[];
  teams: AfmTeam[];
}

/** Response from `POST /afm/apply`. */
export interface AfmApplyResult {
  ok: boolean;
  message: string;
  moved: string[];
  skipped: string[];
}

/** Response from `POST /afm/archive-team-run`. */
export interface AfmArchiveResult {
  ok: boolean;
  folder: string;
  message: string;
}
