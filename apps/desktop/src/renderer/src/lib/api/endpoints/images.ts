/** images endpoints. */
import { requestJson } from "../http";
import type {
  ComfyUIStatus,
  ComfyUISettingsUpdate,
  ComfyUISettings,
  PromptTestResult,
  ImageGeneration,
  ImageGenerateRequest,
} from "../types";


/** `GET /comfyui/status` — local ComfyUI status. */
export function getComfyUIStatus(): Promise<ComfyUIStatus> {
  return requestJson<ComfyUIStatus>("/comfyui/status");
}

/** `PUT /comfyui/settings` — update ComfyUI settings. */
export function updateComfyUISettings(body: ComfyUISettingsUpdate): Promise<ComfyUISettings> {
  return requestJson<ComfyUISettings>("/comfyui/settings", { method: "PUT", body });
}

/** `POST /comfyui/prompt/test` — test connectivity + workflow. */
export function testComfyUIPrompt(prompt: string, negativePrompt = ""): Promise<PromptTestResult> {
  return requestJson<PromptTestResult>("/comfyui/prompt/test", {
    method: "POST",
    body: { prompt, negative_prompt: negativePrompt },
    timeoutMs: 15_000,
  });
}

/** `GET /images` — image generation history. */
export function getImages(): Promise<ImageGeneration[]> {
  return requestJson<ImageGeneration[]>("/images");
}

/** `POST /images/generate` — generate an image (can take a while). */
export function generateImage(body: ImageGenerateRequest): Promise<ImageGeneration> {
  return requestJson<ImageGeneration>("/images/generate", {
    method: "POST",
    body,
    timeoutMs: 300_000,
  });
}

