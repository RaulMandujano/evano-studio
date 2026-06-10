/**
 * The Agent Engine API client.
 *
 * Each backend domain lives in its own module under `endpoints/` (built on the
 * `requestJson` transport in `http.ts`). This file simply composes them into a
 * single `backendApi` namespace that the renderer uses everywhere, so adding a
 * route means editing one small, focused endpoint file — not this one.
 */
import * as health from "./endpoints/health";
import * as ollama from "./endpoints/ollama";
import * as agents from "./endpoints/agents";
import * as documents from "./endpoints/documents";
import * as knowledge from "./endpoints/knowledge";
import * as tools from "./endpoints/tools";
import * as system from "./endpoints/system";
import * as teams from "./endpoints/teams";
import * as openclaw from "./endpoints/openclaw";
import * as routines from "./endpoints/routines";
import * as logs from "./endpoints/logs";
import * as images from "./endpoints/images";
import * as activity from "./endpoints/activity";
import * as org from "./endpoints/org";
import * as afm from "./endpoints/afm";

export const backendApi = {
  ...health,
  ...ollama,
  ...agents,
  ...documents,
  ...knowledge,
  ...tools,
  ...system,
  ...teams,
  ...openclaw,
  ...routines,
  ...logs,
  ...images,
  ...activity,
  ...org,
  ...afm,
};

export { backendBaseUrl } from "../config";
