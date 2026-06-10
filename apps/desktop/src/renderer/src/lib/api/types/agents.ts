/**
 * Built-in Evano agents: CRUD, chat, tool execution, and approvals.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

/** A local agent (from `GET /agents`). */
export interface Agent {
  id: number;
  name: string;
  description: string;
  system_prompt: string;
  model_name: string;
  temperature: number;
  is_enabled: boolean;
  knowledge_enabled: boolean;
  image_enabled: boolean;
  enabled_tools: string[];
  created_at: string;
  updated_at: string;
}

/** Body for creating an agent. */
export interface AgentCreate {
  name: string;
  model_name: string;
  description?: string;
  system_prompt?: string;
  temperature?: number;
  is_enabled?: boolean;
  knowledge_enabled?: boolean;
  image_enabled?: boolean;
  enabled_tools?: string[];
}

/** Body for updating an agent (all fields optional). */
export type AgentUpdate = Partial<AgentCreate>;

/** A ready-made agent starting point (from `GET /agents/templates`). */
export interface AgentTemplate {
  id: string;
  name: string;
  icon: string;
  description: string;
  system_prompt: string;
  temperature: number;
  knowledge_enabled: boolean;
  enabled_tools: string[];
  model_name: string | null;
}

/** A single chat turn sent as history. */
export interface AgentChatMessage {
  role: "user" | "assistant";
  content: string;
}

/** A knowledge-base snippet used to ground a reply (RAG). */
export interface ChatSource {
  title: string | null;
  file_name: string | null;
  snippet: string;
  distance: number | null;
}

/** A tool the agent ran during a chat turn (deterministic tool calling). */
export interface ToolExecution {
  tool_id: string;
  tool_name: string;
  ok: boolean;
  summary: string;
  result: unknown;
  message: string | null;
}

/** A sensitive action the agent proposed that needs your approval. */
export interface PendingAction {
  id: number;
  agent_id: number | null;
  agent_name: string | null;
  tool_id: string;
  tool_name: string;
  summary: string;
  preview: string;
  status: string;
  created_at: string;
}

/** Response from `POST /actions/{id}/approve` and `/deny`. */
export interface ActionResolveResponse {
  ok: boolean;
  status: string;
  execution: ToolExecution | null;
  message: string | null;
}

/** Response from `POST /agents/{id}/chat`. */
export interface AgentChatResponse {
  ok: boolean;
  reply: string | null;
  model: string;
  latency_ms: number | null;
  message: string | null;
  sources: ChatSource[] | null;
  /** Set when the message was handled by a deterministic tool action. */
  tool_execution: ToolExecution | null;
  /** Set when the agent proposed a sensitive action awaiting your approval. */
  pending_action: PendingAction | null;
}

/** Response from `POST /agents/{id}/image-prompt`. */
export interface AgentImagePromptResponse {
  ok: boolean;
  prompt: string;
  model: string;
  latency_ms: number | null;
  message: string | null;
}

