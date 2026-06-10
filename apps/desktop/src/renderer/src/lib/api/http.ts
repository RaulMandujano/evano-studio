/**
 * Core HTTP transport for the Agent Engine API.
 *
 * A tiny fetch wrapper with per-request timeouts and typed errors. Every
 * endpoint module builds on `requestJson`; nothing here knows about specific
 * routes, keeping transport concerns separate from the API surface.
 */
import { backendBaseUrl } from "../config";
import { ApiError } from "./types";

const DEFAULT_TIMEOUT_MS = 4000;

export interface RequestOptions {
  method?: string;
  body?: unknown;
  timeoutMs?: number;
}

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, timeoutMs = DEFAULT_TIMEOUT_MS } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(`${backendBaseUrl}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch {
    // Distinguish a deliberate timeout abort from a generic network failure.
    if (controller.signal.aborted) {
      throw new ApiError("timeout", `Request to ${path} timed out.`);
    }
    throw new ApiError("network", `Could not reach the backend at ${backendBaseUrl}.`);
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    // Surface the backend's structured error message when available.
    let detail = `Backend returned HTTP ${response.status}.`;
    try {
      const errBody = (await response.json()) as { error?: { message?: string } };
      if (errBody?.error?.message) detail = errBody.error.message;
    } catch {
      /* keep the generic message */
    }
    throw new ApiError("http", detail, response.status);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("invalid", "Backend returned an invalid response.");
  }
}
