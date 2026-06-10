#!/usr/bin/env node
/**
 * `pnpm dev` helper.
 *
 * There is no single combined dev runner yet (that would require a process
 * orchestrator we are intentionally not adding during Phase 1). This script
 * prints the available per-target dev commands so the workflow is discoverable.
 */
const lines = [
  "",
  "Evano Studio — development commands",
  "===================================",
  "",
  "  pnpm dev:desktop        Start the desktop app        (apps/desktop)",
  "  pnpm dev:website        Start the website            (apps/website)",
  "  pnpm dev:agent-engine   Start the Python backend     (services/agent-engine)",
  "",
  "  pnpm lint               Lint all workspaces (when configured)",
  "  pnpm test               Test all workspaces (when configured)",
  "  pnpm format             Format all workspaces (when configured)",
  "",
  "Note: the project is in early development. Most targets are placeholders",
  "until their phase begins — see docs/ROADMAP.md.",
  "",
];
console.log(lines.join("\n"));
