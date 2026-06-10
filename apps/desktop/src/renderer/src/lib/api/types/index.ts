/**
 * Public API types for the local backend (Agent Engine), split by domain.
 *
 * Import from `lib/api/types` — this barrel re-exports every domain module so
 * call sites stay stable while each domain lives in its own small file.
 */
export * from "./health";
export * from "./ollama";
export * from "./agents";
export * from "./documents";
export * from "./knowledge";
export * from "./tools";
export * from "./workspace";
export * from "./openclaw";
export * from "./teams";
export * from "./discord";
export * from "./system";
export * from "./routines";
export * from "./images";
export * from "./logs";
export * from "./activity";
export * from "./org";
export * from "./afm";
export * from "./errors";
