/** teams endpoints. */
import { requestJson } from "../http";
import type {
  Team,
  TeamCreate,
} from "../types";


/** `GET /teams` — saved team workflows. */
export function getTeams(): Promise<Team[]> {
  return requestJson<Team[]>("/teams");
}

/** `POST /teams` — create a team. */
export function createTeam(body: TeamCreate): Promise<Team> {
  return requestJson<Team>("/teams", { method: "POST", body });
}

/** `PUT /teams/{id}` — update a team. */
export function updateTeam(id: number, body: Partial<TeamCreate>): Promise<Team> {
  return requestJson<Team>(`/teams/${id}`, { method: "PUT", body });
}

/** `DELETE /teams/{id}` — delete a team. */
export function deleteTeam(id: number): Promise<{ ok: boolean }> {
  return requestJson<{ ok: boolean }>(`/teams/${id}`, { method: "DELETE" });
}

/** `GET /openclaw/status` — Node/Ollama/OpenClaw presence + config + ready. */
