/**
 * Local image generation via ComfyUI.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

// ---- ComfyUI / images -----------------------------------------------------

/** Response from `GET /comfyui/status`. */
export interface ComfyUIStatus {
  enabled: boolean;
  base_url: string;
  reachable: boolean;
  version: string | null;
  default_workflow_path: string;
  message: string | null;
}

/** Body for `PUT /comfyui/settings`. */
export interface ComfyUISettingsUpdate {
  base_url?: string;
  enabled?: boolean;
  default_workflow_path?: string;
}

/** Response from `PUT /comfyui/settings`. */
export interface ComfyUISettings {
  base_url: string;
  enabled: boolean;
  default_workflow_path: string;
}

/** Response from `POST /comfyui/prompt/test`. */
export interface PromptTestResult {
  ok: boolean;
  reachable: boolean;
  message: string | null;
}

/** An image generation record (from `GET /images`). */
export interface ImageGeneration {
  id: number;
  prompt: string;
  negative_prompt: string | null;
  workflow_name: string | null;
  status: string;
  output_path: string | null;
  error: string | null;
  created_by_agent_id: number | null;
  created_at: string;
  updated_at: string;
}

/** Body for `POST /images/generate`. */
export interface ImageGenerateRequest {
  prompt: string;
  negative_prompt?: string;
  workflow_name?: string;
  agent_id?: number | null;
}

