/**
 * Ollama (local model runtime) status, models, and downloads.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

/** A locally installed Ollama model (from `GET /ollama/models`). */
export interface OllamaModel {
  name: string;
  size_bytes: number | null;
  modified_at: string | null;
  family: string | null;
  parameter_size: string | null;
  digest: string | null;
}

/** Response from `GET /ollama/status`. */
export interface OllamaStatus {
  status: "running" | "offline" | "error";
  reachable: boolean;
  base_url: string;
  version: string | null;
  model_count: number;
  recommended_model: string;
  recommended_available: boolean;
  message: string | null;
}

/** Response from `GET /ollama/models`. */
export interface OllamaModelsResponse {
  reachable: boolean;
  models: OllamaModel[];
  count: number;
  recommended_model: string;
  recommended_available: boolean;
  message: string | null;
}

/** A curated model the user can install (from `GET /ollama/models/recommended`). */
export interface RecommendedModel {
  model: string;
  name: string;
  category: string;
  notes: string;
  family: string | null;
  size_estimate: string | null;
  min_ram: string | null;
  recommended: boolean;
  installed: boolean;
}

/** Response from `GET /ollama/models/recommended`. */
export interface RecommendedModelsResponse {
  reachable: boolean;
  recommended_model: string;
  models: RecommendedModel[];
  message: string | null;
}

export type PullState = "idle" | "pending" | "downloading" | "success" | "error";

/** Progress of a model pull (from `POST /ollama/models/pull` and its status). */
export interface PullStatus {
  model: string;
  state: PullState;
  percent: number;
  completed_bytes: number;
  total_bytes: number;
  detail: string | null;
  message: string | null;
  updated_at: string | null;
}

