/** openclaw endpoints. */
import { requestJson } from "../http";
import type {
  OpenClawStatus,
  OpenClawInstallStatus,
  OpenClawConfigResult,
  GatewayActionResult,
  DashboardUrlResponse,
  WebSearchResult,
  ChannelsResponse,
  ChannelActionResult,
  OpenClawAgentsResponse,
  OpenClawAgentResult,
  AgentActionResult,
  AgentChatResult,
  AgentDiscordResult,
  AgentDiscordStatus,
  AgentDocumentContent,
  AgentDocumentsResponse,
  AgentFilesResponse,
  AllChatsResponse,
  SessionsResponse,
  SessionDetail,
  ClearSessionsResult,
  FileHandoffResult,
} from "../types";

export function getOpenClawStatus(): Promise<OpenClawStatus> {
  return requestJson<OpenClawStatus>("/openclaw/status");
}

/** `POST /openclaw/file-handoff` — copy a working file from one agent to another. */
export function handoffOpenClawFile(body: {
  from_agent_id: string;
  to_agent_id: string;
  file_name: string;
}): Promise<FileHandoffResult> {
  return requestJson<FileHandoffResult>("/openclaw/file-handoff", {
    method: "POST",
    body,
    timeoutMs: 30_000,
  });
}

/** `POST /openclaw/install` — start installing OpenClaw via npm (non-blocking). */
export function installOpenClaw(): Promise<OpenClawInstallStatus> {
  return requestJson<OpenClawInstallStatus>("/openclaw/install", { method: "POST" });
}

/** `GET /openclaw/install/status` — install progress. */
export function getOpenClawInstallStatus(): Promise<OpenClawInstallStatus> {
  return requestJson<OpenClawInstallStatus>("/openclaw/install/status");
}

/** `POST /openclaw/config` — configure OpenClaw (free Gemma 4, or API key). */
export function writeOpenClawConfig(body: {
  mode: "free" | "api";
  model?: string;
  provider?: string;
  api_key?: string;
  base_url?: string;
}): Promise<OpenClawConfigResult> {
  // Onboarding can take a while (validates/sets up the workspace).
  return requestJson<OpenClawConfigResult>("/openclaw/config", {
    method: "POST",
    body,
    timeoutMs: 200_000,
  });
}

/** `POST /openclaw/gateway/start` — start the OpenClaw gateway. */
export function startOpenClawGateway(): Promise<GatewayActionResult> {
  return requestJson<GatewayActionResult>("/openclaw/gateway/start", { method: "POST", timeoutMs: 70_000 });
}

/** `POST /openclaw/gateway/stop` — stop the OpenClaw gateway. */
export function stopOpenClawGateway(): Promise<GatewayActionResult> {
  return requestJson<GatewayActionResult>("/openclaw/gateway/stop", { method: "POST", timeoutMs: 70_000 });
}

/** `GET /openclaw/dashboard` — token-authenticated dashboard URL. */
export function getOpenClawDashboardUrl(): Promise<DashboardUrlResponse> {
  return requestJson<DashboardUrlResponse>("/openclaw/dashboard", { timeoutMs: 70_000 });
}

/** `POST /openclaw/web-search/enable` — turn on free DuckDuckGo web search. */
export function enableOpenClawWebSearch(): Promise<WebSearchResult> {
  return requestJson<WebSearchResult>("/openclaw/web-search/enable", { method: "POST", timeoutMs: 70_000 });
}

/** `GET /openclaw/channels` — messaging platforms + connection state. */
export function getOpenClawChannels(): Promise<ChannelsResponse> {
  return requestJson<ChannelsResponse>("/openclaw/channels", { timeoutMs: 40_000 });
}

/** `POST /openclaw/channels/add` — connect a channel with a token. */
export function addOpenClawChannel(body: { channel: string; token: string }): Promise<ChannelActionResult> {
  return requestJson<ChannelActionResult>("/openclaw/channels/add", {
    method: "POST",
    body,
    timeoutMs: 70_000,
  });
}

/** `GET /openclaw/agents` — agents that run inside OpenClaw. */
export function getOpenClawAgents(): Promise<OpenClawAgentsResponse> {
  return requestJson<OpenClawAgentsResponse>("/openclaw/agents", { timeoutMs: 40_000 });
}

/** `POST /openclaw/agents` — create an OpenClaw agent (Gemma 4 by default). */
export function createOpenClawAgent(body: {
  name: string;
  model?: string;
  instructions?: string;
  emoji?: string;
}): Promise<OpenClawAgentResult> {
  return requestJson<OpenClawAgentResult>("/openclaw/agents", { method: "POST", body, timeoutMs: 90_000 });
}

/** `DELETE /openclaw/agents/{id}` — delete an OpenClaw agent. */
export function deleteOpenClawAgent(id: string): Promise<AgentActionResult> {
  return requestJson<AgentActionResult>(`/openclaw/agents/${encodeURIComponent(id)}`, {
    method: "DELETE",
    timeoutMs: 70_000,
  });
}

/** `POST /openclaw/agents/{id}/chat` — one native agent turn (can be slow). A
 *  stable sessionId keeps conversation continuity (the agent remembers). The
 *  optional activity label/kind is what the Office view shows while it runs. */
export function chatOpenClawAgent(
  id: string,
  message: string,
  sessionId?: string,
  activity?: { task: string; kind: "chat" | "team" },
): Promise<AgentChatResult> {
  return requestJson<AgentChatResult>(`/openclaw/agents/${encodeURIComponent(id)}/chat`, {
    method: "POST",
    body: {
      message,
      session_id: sessionId,
      activity_task: activity?.task,
      activity_kind: activity?.kind,
    },
    timeoutMs: 240_000,
  });
}

/** `GET /openclaw/agents/{id}/discord` — is this agent live as its own Discord bot? */
export function getAgentDiscordStatus(id: string): Promise<AgentDiscordStatus> {
  return requestJson<AgentDiscordStatus>(`/openclaw/agents/${encodeURIComponent(id)}/discord`, {
    timeoutMs: 40_000,
  });
}

/** `POST /openclaw/agents/{id}/discord` — register the bot token + bind + reload gateway. */
export function connectAgentDiscord(id: string, botToken: string): Promise<AgentDiscordResult> {
  return requestJson<AgentDiscordResult>(`/openclaw/agents/${encodeURIComponent(id)}/discord`, {
    method: "POST",
    body: { bot_token: botToken },
    timeoutMs: 120_000, // may restart the gateway
  });
}

/** `DELETE /openclaw/agents/{id}/discord` — unlink the bot and remove its account. */
export function disconnectAgentDiscord(id: string): Promise<AgentDiscordResult> {
  return requestJson<AgentDiscordResult>(`/openclaw/agents/${encodeURIComponent(id)}/discord`, {
    method: "DELETE",
    timeoutMs: 120_000,
  });
}

/** `GET /openclaw/agents/{id}/files` — the agent's config files (IDENTITY/AGENTS/…). */
export function getOpenClawAgentFiles(id: string): Promise<AgentFilesResponse> {
  return requestJson<AgentFilesResponse>(`/openclaw/agents/${encodeURIComponent(id)}/files`, {
    timeoutMs: 40_000,
  });
}

/** `PUT /openclaw/agents/{id}/files/{name}` — save a config file. */
export function saveOpenClawAgentFile(id: string, name: string, content: string): Promise<AgentActionResult> {
  return requestJson<AgentActionResult>(
    `/openclaw/agents/${encodeURIComponent(id)}/files/${encodeURIComponent(name)}`,
    { method: "PUT", body: { content }, timeoutMs: 40_000 },
  );
}

/** `GET /openclaw/documents` — agent work files, grouped by agent. */
export function getAgentDocuments(): Promise<AgentDocumentsResponse> {
  return requestJson<AgentDocumentsResponse>("/openclaw/documents", { timeoutMs: 40_000 });
}

/** `GET /openclaw/documents/content` — bounded text preview of a work file. */
export function getAgentDocumentContent(agentId: string, path: string): Promise<AgentDocumentContent> {
  const qs = `agent_id=${encodeURIComponent(agentId)}&path=${encodeURIComponent(path)}`;
  return requestJson<AgentDocumentContent>(`/openclaw/documents/content?${qs}`, { timeoutMs: 40_000 });
}

/** `DELETE /openclaw/documents/content` — delete an agent work file. */
export function deleteAgentDocument(agentId: string, path: string): Promise<AgentActionResult> {
  const qs = `agent_id=${encodeURIComponent(agentId)}&path=${encodeURIComponent(path)}`;
  return requestJson<AgentActionResult>(`/openclaw/documents/content?${qs}`, {
    method: "DELETE",
    timeoutMs: 40_000,
  });
}

/** `GET /openclaw/chats` — every conversation of every agent, with origins. */
export function getAllChats(): Promise<AllChatsResponse> {
  return requestJson<AllChatsResponse>("/openclaw/chats", { timeoutMs: 40_000 });
}

/** `GET /openclaw/agents/{id}/sessions` — saved conversation history. */
export function getOpenClawSessions(id: string): Promise<SessionsResponse> {
  return requestJson<SessionsResponse>(`/openclaw/agents/${encodeURIComponent(id)}/sessions`, {
    timeoutMs: 40_000,
  });
}

/** `GET /openclaw/agents/{id}/sessions/{sid}` — load a past conversation. */
export function getOpenClawSession(id: string, sessionId: string): Promise<SessionDetail> {
  return requestJson<SessionDetail>(
    `/openclaw/agents/${encodeURIComponent(id)}/sessions/${encodeURIComponent(sessionId)}`,
    { timeoutMs: 40_000 },
  );
}

/** `DELETE /openclaw/agents/{id}/sessions/{sid}` — delete one conversation. */
export function deleteOpenClawSession(id: string, sessionId: string): Promise<AgentActionResult> {
  return requestJson<AgentActionResult>(
    `/openclaw/agents/${encodeURIComponent(id)}/sessions/${encodeURIComponent(sessionId)}`,
    { method: "DELETE", timeoutMs: 40_000 },
  );
}

/** `POST /openclaw/agents/{id}/sessions/clear` — clear history (optionally only older than N days). */
export function clearOpenClawSessions(id: string, olderThanDays?: number): Promise<ClearSessionsResult> {
  return requestJson<ClearSessionsResult>(`/openclaw/agents/${encodeURIComponent(id)}/sessions/clear`, {
    method: "POST",
    body: { older_than_days: olderThanDays ?? null },
    timeoutMs: 40_000,
  });
}

/** `GET /settings` — all app settings. */
