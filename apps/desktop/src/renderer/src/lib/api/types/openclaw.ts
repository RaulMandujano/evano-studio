/**
 * OpenClaw control: install, config, gateway, channels, agents, sessions, files, web search.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- OpenClaw control -----------------------------------------------------

export interface ToolPresence {
  installed: boolean;
  version: string | null;
}

export interface OpenClawConfigSummary {
  exists: boolean;
  path: string;
  provider: string | null;
  model: string | null;
}

export interface GatewayInfo {
  running: boolean;
  port: number;
}

export interface WebSearchInfo {
  provider: string | null;
  enabled: boolean;
}

/** Response from `GET /openclaw/status`. */
export interface OpenClawStatus {
  node: ToolPresence;
  npm: ToolPresence;
  ollama: ToolPresence;
  openclaw: ToolPresence;
  config: OpenClawConfigSummary;
  gateway: GatewayInfo;
  web_search: WebSearchInfo;
  ready: boolean;
}

/** Response from `POST /openclaw/web-search/enable`. */
export interface WebSearchResult {
  ok: boolean;
  message: string;
  web_search: WebSearchInfo;
}

/** Response from `POST /openclaw/install` and `GET /openclaw/install/status`. */
export interface OpenClawInstallStatus {
  state: string; // idle | running | success | error
  message: string;
  log_tail: string;
}

/** A prerequisite Evano can install for you (download + launch official installer). */
export type PrereqTarget = "node" | "ollama";

/** Response from `/openclaw/prereqs/{target}/install[/status]`. */
export interface PrereqInstallStatus {
  state: string; // idle | downloading | launching | launched | error
  message: string;
  percent: number;
  download_url: string; // official page, manual fallback
}

/** Response from `POST /openclaw/config`. */
export interface OpenClawConfigResult {
  ok: boolean;
  message: string;
  config: OpenClawConfigSummary;
}

/** Response from `POST /openclaw/gateway/{start,stop}`. */
export interface GatewayActionResult {
  ok: boolean;
  message: string;
  running: boolean;
}

/** Response from `GET /openclaw/dashboard`. */
export interface DashboardUrlResponse {
  ok: boolean;
  url: string | null;
  message: string;
}


/** A messaging platform OpenClaw can connect to (WhatsApp, Discord, …). */
export interface OpenClawChannel {
  slug: string;
  name: string;
  icon: string;
  connect: "token" | "login";
  can_add: boolean;
  installed: boolean;
  configured: boolean;
  popular: boolean;
}

/** Response from `GET /openclaw/channels`. */
export interface ChannelsResponse {
  ok: boolean;
  message: string;
  channels: OpenClawChannel[];
}

/** Response from `POST /openclaw/channels/add`. */
export interface ChannelActionResult {
  ok: boolean;
  message: string;
}

/** An OpenClaw agent (runs inside OpenClaw, with its own workspace + model). */
export interface OpenClawAgent {
  id: string;
  name: string;
  model: string;
  workspace: string;
  is_default: boolean;
  bindings: number;
}

/** Response from `GET /openclaw/agents`. */
export interface OpenClawAgentsResponse {
  ok: boolean;
  message: string;
  agents: OpenClawAgent[];
}

/** Response from `POST /openclaw/agents`. */
export interface OpenClawAgentResult {
  ok: boolean;
  message: string;
  agent: OpenClawAgent | null;
}

/** Response from `DELETE /openclaw/agents/{id}` and file saves. */
export interface AgentActionResult {
  ok: boolean;
  message: string;
}

/** Response from `POST /openclaw/file-handoff` (copy a file agent→agent). */
export interface FileHandoffResult {
  ok: boolean;
  message: string;
  path?: string | null;
}

/** Response from `POST /openclaw/agents/{id}/chat`. */
export interface AgentChatResult {
  ok: boolean;
  reply: string;
  model: string;
  session_id: string;
  message: string;
}

/** A work file an agent created in its workspace. */
export interface AgentWorkFile {
  name: string;
  path: string; // relative to the agent's workspace
  size_bytes: number;
  modified_at: number; // epoch ms
  abs_path: string;
}

/** One agent's work files (the Documents tab). */
export interface AgentDocumentsGroup {
  agent_id: string;
  name: string;
  emoji: string;
  files: AgentWorkFile[];
}

/** Response from `GET /openclaw/documents`. */
export interface AgentDocumentsResponse {
  ok: boolean;
  message: string;
  agents: AgentDocumentsGroup[];
}

/** Response from `GET /openclaw/documents/content`. */
export interface AgentDocumentContent {
  ok: boolean;
  message: string;
  name: string;
  content: string;
  truncated: boolean;
}

/** Response from `GET /openclaw/agents/{id}/discord`. */
export interface AgentDiscordStatus {
  ok: boolean;
  connected: boolean;
  account_id: string;
  gateway_running: boolean;
  message: string;
}

/** Response from `POST/DELETE /openclaw/agents/{id}/discord`. */
export interface AgentDiscordResult {
  ok: boolean;
  message: string;
}

/** One config file in an OpenClaw agent's workspace. */
export interface AgentFile {
  name: string;
  label: string;
  size: number;
  content: string;
  exists: boolean;
}

/** Response from `GET /openclaw/agents/{id}/files`. */
export interface AgentFilesResponse {
  ok: boolean;
  message: string;
  workspace: string;
  files: AgentFile[];
}

/** Where a conversation came from. */
export type ChatOrigin =
  | "evano"
  | "team"
  | "discord"
  | "telegram"
  | "whatsapp"
  | "slack"
  | "signal"
  | "imessage"
  | "dashboard"
  | "subagent"
  | "cron"
  | "other";

/** A saved conversation with an agent. */
export interface SessionSummary {
  session_id: string;
  preview: string;
  message_count: number;
  updated_at: number; // epoch ms
  size_bytes: number;
  origin: ChatOrigin;
}

/** One agent's conversations (the Chats tab). */
export interface AgentChats {
  agent_id: string;
  name: string;
  emoji: string;
  sessions: SessionSummary[];
}

/** Response from `GET /openclaw/chats`. */
export interface AllChatsResponse {
  ok: boolean;
  message: string;
  agents: AgentChats[];
}

/** Response from `GET /openclaw/agents/{id}/sessions`. */
export interface SessionsResponse {
  ok: boolean;
  message: string;
  sessions: SessionSummary[];
  total_bytes: number;
}

/** Response from `GET /openclaw/agents/{id}/sessions/{sid}`. */
export interface SessionDetail {
  ok: boolean;
  message: string;
  messages: { role: "user" | "assistant"; content: string }[];
}

/** Response from `POST /openclaw/agents/{id}/sessions/clear`. */
export interface ClearSessionsResult {
  ok: boolean;
  message: string;
  deleted: number;
  freed_bytes: number;
}


/** A customer-facing channel offered in the Customer Service setup. */
export interface SupportChannel {
  slug: string;
  name: string;
  icon: string;
  connect: "token" | "login";
  configured: boolean;
}

/** A live routing: this channel's messages go to this agent. */
export interface SupportAssignment {
  agent_id: string;
  channel: string;
  account_id: string;
}

export interface SupportAgentLite {
  id: string;
  name: string;
  emoji: string;
}

/** Response from `GET /openclaw/support/status`. */
export interface CustomerServiceStatus {
  ok: boolean;
  message: string;
  gateway_running: boolean;
  agents: SupportAgentLite[];
  channels: SupportChannel[];
  assignments: SupportAssignment[];
}

/** Response from the in-app WhatsApp pairing endpoints. */
export interface WhatsAppLoginStatus {
  state: "idle" | "starting" | "qr" | "connected" | "error" | "expired";
  qr_svg: string | null;
  message: string;
}
