/** health endpoints. */
import { requestJson } from "../http";
import type {
  HealthResponse,
} from "../types";

/** `GET /health` — used to detect whether the Agent Engine is running. */
export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

/** `GET /ollama/status` — local Ollama runtime status (via the backend). */
