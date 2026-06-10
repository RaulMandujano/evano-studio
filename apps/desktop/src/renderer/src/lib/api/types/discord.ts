/**
 * Discord channel bridge.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- Discord channel ------------------------------------------------------

/** Response from `GET /discord/status`. */
export interface DiscordStatus {
  available: boolean;
  enabled: boolean;
  configured: boolean;
  state: string; // stopped | starting | running | error | disabled
  agent_id: number | null;
  allowed_count: number;
  message: string | null;
}

