/** org chart endpoints — the chain of command between agents. */
import { requestJson } from "../http";
import type { OrgActionResult, OrgChartResponse, OrgLinkItem } from "../types";

/** `GET /org/chart` — agents + saved reporting lines. */
export function getOrgChart(): Promise<OrgChartResponse> {
  return requestJson<OrgChartResponse>("/org/chart", { timeoutMs: 40_000 });
}

/** `PUT /org/chart` — validate, save, and APPLY the chart (permissions + team
 *  notes + gateway reload). May restart the gateway, hence the long timeout. */
export function saveOrgChart(links: OrgLinkItem[]): Promise<OrgActionResult> {
  return requestJson<OrgActionResult>("/org/chart", {
    method: "PUT",
    body: { links },
    timeoutMs: 120_000,
  });
}
