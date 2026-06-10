/**
 * API error type — distinguishes offline from real errors.
 *
 * Mirrors the FastAPI schemas in `services/agent-engine/app/schemas`.
 */

export type ApiErrorKind =
  | "network" // could not reach the backend at all
  | "timeout" // request took too long
  | "http" // reached the backend, but it returned a non-2xx status
  | "invalid"; // reached the backend, but the response was unparseable

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly statusCode?: number;

  constructor(kind: ApiErrorKind, message: string, statusCode?: number) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.statusCode = statusCode;
  }

  /** True when the backend simply isn't reachable (vs. a real error). */
  get isUnreachable(): boolean {
    return this.kind === "network" || this.kind === "timeout";
  }
}
