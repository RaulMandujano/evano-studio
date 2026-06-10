/** agents endpoints. */
import { requestJson } from "../http";
import type {
  Agent,
  AgentTemplate,
  AgentCreate,
  AgentUpdate,
  AgentChatMessage,
  AgentChatResponse,
  AgentImagePromptResponse,
  ImageGeneration,
} from "../types";


/** `GET /agents` — list all agents. */
export function getAgents(): Promise<Agent[]> {
  return requestJson<Agent[]>("/agents");
}

/** `GET /agents/templates` — ready-made agent starting points. */
export function getAgentTemplates(): Promise<AgentTemplate[]> {
  return requestJson<AgentTemplate[]>("/agents/templates");
}

/** `POST /agents` — create an agent. */
export function createAgent(body: AgentCreate): Promise<Agent> {
  return requestJson<Agent>("/agents", { method: "POST", body });
}

/** `PUT /agents/{id}` — update an agent. */
export function updateAgent(id: number, body: AgentUpdate): Promise<Agent> {
  return requestJson<Agent>(`/agents/${id}`, { method: "PUT", body });
}

/** `DELETE /agents/{id}` — delete an agent. */
export function deleteAgent(id: number): Promise<{ ok: boolean }> {
  return requestJson<{ ok: boolean }>(`/agents/${id}`, { method: "DELETE" });
}

/** `POST /agents/{id}/chat` — one chat turn (longer timeout for inference). */
export function chatWithAgent(
  id: number,
  message: string,
  history: AgentChatMessage[] = [],
): Promise<AgentChatResponse> {
  return requestJson<AgentChatResponse>(`/agents/${id}/chat`, {
    method: "POST",
    body: { message, history },
    timeoutMs: 120_000,
  });
}

/** `POST /agents/{id}/image-prompt` — agent crafts an image prompt (Ollama). */
export function createAgentImagePrompt(
  id: number,
  body: { idea: string; style?: string; details?: string },
): Promise<AgentImagePromptResponse> {
  return requestJson<AgentImagePromptResponse>(`/agents/${id}/image-prompt`, {
    method: "POST",
    body,
    timeoutMs: 120_000,
  });
}

/** `POST /agents/{id}/generate-image` — generate via ComfyUI (image-enabled agent). */
export function generateAgentImage(
  id: number,
  body: { prompt: string; negative_prompt?: string; workflow_name?: string },
): Promise<ImageGeneration> {
  return requestJson<ImageGeneration>(`/agents/${id}/generate-image`, {
    method: "POST",
    body,
    timeoutMs: 300_000,
  });
}

