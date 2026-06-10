/**
 * The Office — a live visual of your agents as office workers.
 *
 * Agents doing work (a chat, a team step, a routine) sit at their desk with a
 * task bubble; idle agents hang out in the break room; disabled agents nap.
 * Powered by polling `GET /activity` while this view is open.
 */
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Desk } from "../components/office/Desk";
import { BreakRoom } from "../components/office/BreakRoom";
import { ActivityFeed } from "../components/office/ActivityFeed";
import { useBackendResource } from "../hooks/useBackendResource";
import { useOfficeActivity } from "../hooks/useOfficeActivity";
import { backendApi } from "../lib/api/client";
import { buildWorkers } from "../lib/office";
import { useNavigate } from "../navigation-context";

export function OfficeView() {
  const navigate = useNavigate();
  const openclawRes = useBackendResource(backendApi.getOpenClawAgents, "oc-agents");
  const builtinRes = useBackendResource(backendApi.getAgents, "builtin-agents");
  const { state, snapshot } = useOfficeActivity();

  if (state === "offline") {
    return (
      <div>
        <PageHeader icon="🏢" title="Office" subtitle="Watch your agents work, live." />
        <Card>
          <div className="office-closed">
            <span className="office-closed-icon">🌙</span>
            <h3>The office is closed</h3>
            <p className="muted">
              The Evano Engine isn&apos;t running, so nobody can come to work. Start the backend and
              the lights come back on.
            </p>
            <Button onClick={() => navigate("settings")}>Open Settings</Button>
          </div>
        </Card>
      </div>
    );
  }

  const workers = buildWorkers(
    openclawRes.data?.agents ?? [],
    builtinRes.data ?? [],
    snapshot?.active ?? [],
  );
  const onDuty = workers.filter((w) => !w.offDuty);
  const busy = onDuty.filter((w) => w.working);
  const idle = onDuty.filter((w) => !w.working);
  const offDuty = workers.filter((w) => w.offDuty && !w.working);
  const loadingRoster = openclawRes.state === "checking" || builtinRes.state === "checking";

  return (
    <div>
      <PageHeader
        icon="🏢"
        title="Office"
        subtitle={
          busy.length > 0
            ? `${busy.length} agent${busy.length === 1 ? "" : "s"} working right now.`
            : "Everyone's on break — give them something to do."
        }
      />

      {workers.length === 0 ? (
        <Card>
          <div className="office-closed">
            <span className="office-closed-icon">📦</span>
            <h3>{loadingRoster ? "Opening the office…" : "Nobody works here yet"}</h3>
            {loadingRoster ? null : (
              <>
                <p className="muted">Hire your first agent and it&apos;ll get a desk here.</p>
                <Button variant="primary" onClick={() => navigate("openclaw-agents")}>
                  Create an agent
                </Button>
              </>
            )}
          </div>
        </Card>
      ) : (
        <div className="office-layout">
          <div className="office-floor">
            <div className="office-zone office-zone--work">
              <div className="office-zone-head">
                <h3>🖥️ Desks</h3>
                <p className="muted">A desk per agent — they sit down when they have work.</p>
              </div>
              <div className="office-desk-grid">
                {onDuty.map((w) => (
                  <Desk key={w.key} worker={w} />
                ))}
              </div>
            </div>
            <BreakRoom idle={idle} offDuty={offDuty} />
          </div>
          <ActivityFeed active={snapshot?.active ?? []} recent={snapshot?.recent ?? []} />
        </div>
      )}
    </div>
  );
}
