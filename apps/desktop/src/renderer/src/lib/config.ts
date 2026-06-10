/**
 * Renderer-side configuration.
 *
 * The backend base URL can be overridden at build time with
 * `VITE_EVANO_BACKEND_URL` (see `.env.example`); otherwise it defaults to the
 * local Agent Engine address. Trailing slashes are normalized away.
 */

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8765";

const configured = import.meta.env.VITE_EVANO_BACKEND_URL as string | undefined;

export const backendBaseUrl: string = (configured ?? DEFAULT_BACKEND_URL).replace(
  /\/+$/,
  "",
);
