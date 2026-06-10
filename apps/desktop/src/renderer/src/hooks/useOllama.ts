import { backendApi } from "../lib/api/client";
import type {
  OllamaModelsResponse,
  OllamaStatus,
  RecommendedModelsResponse,
} from "../lib/api/types";
import { useBackendResource, type BackendResource } from "./useBackendResource";

/** Live Ollama runtime status (via the backend). */
export function useOllamaStatus(): BackendResource<OllamaStatus> {
  return useBackendResource<OllamaStatus>(backendApi.getOllamaStatus);
}

/** Locally installed Ollama models (via the backend). */
export function useOllamaModels(): BackendResource<OllamaModelsResponse> {
  return useBackendResource<OllamaModelsResponse>(backendApi.getOllamaModels);
}

/** Curated, installable recommended models (via the backend). */
export function useRecommendedModels(): BackendResource<RecommendedModelsResponse> {
  return useBackendResource<RecommendedModelsResponse>(backendApi.getRecommendedModels);
}
