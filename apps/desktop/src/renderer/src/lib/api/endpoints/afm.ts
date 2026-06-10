/** AFM endpoints — where each agent's content lives on disk. */
import { requestJson } from "../http";
import type { AfmApplyResult, AfmArchiveResult, AfmStatus } from "../types";

/** `GET /afm/status` — root + per-agent/per-team folder placement. */
export function getAfmStatus(): Promise<AfmStatus> {
  return requestJson<AfmStatus>("/afm/status", { timeoutMs: 40_000 });
}

/** `POST /afm/apply` — choose the root (empty → Evano default) and organize.
 *  Moves agent folders and may restart the gateway, hence the long timeout. */
export function applyAfm(root?: string | null): Promise<AfmApplyResult> {
  return requestJson<AfmApplyResult>("/afm/apply", {
    method: "POST",
    body: { root: root ?? null },
    timeoutMs: 180_000,
  });
}

/** `POST /afm/archive-team-run` — save a finished team run under Teams/<Team>/. */
export function archiveTeamRun(body: {
  team_name: string;
  steps: { agent_id: string; output: string }[];
  final: string;
}): Promise<AfmArchiveResult> {
  return requestJson<AfmArchiveResult>("/afm/archive-team-run", {
    method: "POST",
    body,
    timeoutMs: 60_000,
  });
}
