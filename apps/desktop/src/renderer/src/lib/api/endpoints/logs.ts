/** logs endpoints. */
import { requestJson } from "../http";
import type {
  LogsResponse,
  SupportBundle,
} from "../types";


/** `GET /logs` — recent backend logs (optionally filtered). */
export function getLogs(opts: { limit?: number; level?: string; area?: string } = {}): Promise<LogsResponse> {
  const params = new URLSearchParams();
  if (opts.limit) params.set("limit", String(opts.limit));
  if (opts.level) params.set("level", opts.level);
  if (opts.area) params.set("area", opts.area);
  const qs = params.toString();
  return requestJson<LogsResponse>(`/logs${qs ? `?${qs}` : ""}`);
}

/** `POST /support/bundle` — build + write a privacy-safe support bundle. */
export function createSupportBundle(): Promise<SupportBundle> {
  return requestJson<SupportBundle>("/support/bundle", { method: "POST", timeoutMs: 30_000 });
}

