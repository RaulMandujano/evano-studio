/** ollama endpoints. */
import { requestJson } from "../http";
import type {
  OllamaStatus,
  OllamaModelsResponse,
  RecommendedModelsResponse,
  PullStatus,
} from "../types";

export function getOllamaStatus(): Promise<OllamaStatus> {
  return requestJson<OllamaStatus>("/ollama/status");
}

/** `GET /ollama/models` — locally installed Ollama models (via the backend). */
export function getOllamaModels(): Promise<OllamaModelsResponse> {
  return requestJson<OllamaModelsResponse>("/ollama/models");
}

/** `GET /ollama/models/recommended` — curated free models to install. */
export function getRecommendedModels(): Promise<RecommendedModelsResponse> {
  return requestJson<RecommendedModelsResponse>("/ollama/models/recommended");
}

/** `POST /ollama/models/pull` — start installing a model (non-blocking). */
export function startModelPull(model: string): Promise<PullStatus> {
  return requestJson<PullStatus>("/ollama/models/pull", { method: "POST", body: { model } });
}

/** `GET /ollama/models/pull/status` — poll a model's install progress. */
export function getPullStatus(model: string): Promise<PullStatus> {
  return requestJson<PullStatus>(
    `/ollama/models/pull/status?model=${encodeURIComponent(model)}`,
  );
}

