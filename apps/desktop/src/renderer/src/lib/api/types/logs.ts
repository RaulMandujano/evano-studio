/**
 * Logs and the support bundle.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- Logs / support -------------------------------------------------------

/** A structured log entry (from `GET /logs`). */
export interface LogEntry {
  timestamp: string;
  level: string;
  area: string;
  logger: string;
  message: string;
}

/** Response from `GET /logs`. */
export interface LogsResponse {
  entries: LogEntry[];
}

/** Response from `POST /support/bundle`. */
export interface SupportBundle {
  path: string;
  bundle: Record<string, unknown>;
}

/** How an API call failed — lets callers distinguish "offline" from "error". */
