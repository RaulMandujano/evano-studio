/**
 * Health check.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

/** Response from `GET /health`. */
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  uptime_seconds: number;
}

