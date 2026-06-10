import { useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { RoutineForm } from "../components/routines/RoutineForm";
import { RoutineDetailPanel } from "../components/routines/RoutineDetailPanel";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { scheduleSummary } from "../lib/routines";
import type { OpenClawAgentsResponse, Routine, RoutineCreate } from "../lib/api/types";

type Mode = "idle" | "create" | "edit";

export function RoutinesView() {
  const routinesRes = useBackendResource<Routine[]>(backendApi.getRoutines);
  const agentsRes = useBackendResource<OpenClawAgentsResponse>(backendApi.getOpenClawAgents);

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<Mode>("idle");
  const [editing, setEditing] = useState<Routine | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const routines = routinesRes.data ?? [];
  const agents = agentsRes.data?.agents ?? [];

  const submit = async (data: RoutineCreate, id?: number) => {
    setSubmitting(true);
    setFormError(null);
    try {
      const saved = id
        ? await backendApi.updateRoutine(id, data)
        : await backendApi.createRoutine(data);
      routinesRes.refresh();
      setSelectedId(saved.id);
      setMode("idle");
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Couldn't save the routine.");
    } finally {
      setSubmitting(false);
    }
  };

  const renderList = () => {
    if (routinesRes.state === "checking") return <p className="muted">Loading routines…</p>;
    if (routinesRes.state !== "ready") {
      return <p className="muted">Backend offline — start the Agent Engine and refresh.</p>;
    }
    if (routines.length === 0) {
      return <p className="muted">No routines yet. Create one to schedule an agent task.</p>;
    }
    return (
      <ul className="agent-list">
        {routines.map((routine) => (
          <li key={routine.id}>
            <button
              type="button"
              className={`agent-list-item${
                routine.id === selectedId && mode === "idle" ? " is-active" : ""
              }`}
              onClick={() => {
                setSelectedId(routine.id);
                setMode("idle");
              }}
            >
              <span className={`status-dot ${routine.is_enabled ? "is-on" : "is-off"}`} />
              <span className="agent-list-name">{routine.name}</span>
              <span className="agent-list-model">{scheduleSummary(routine)}</span>
            </button>
          </li>
        ))}
      </ul>
    );
  };

  const renderDetail = () => {
    if (mode === "create" || mode === "edit") {
      return (
        <Card>
          <RoutineForm
            initial={mode === "edit" ? editing : null}
            agents={agents}
            submitting={submitting}
            error={formError}
            onSubmit={(data) => submit(data, mode === "edit" ? editing?.id : undefined)}
            onCancel={() => setMode("idle")}
          />
        </Card>
      );
    }
    if (selectedId !== null) {
      return (
        <Card>
          <RoutineDetailPanel
            routineId={selectedId}
            agents={agents}
            onEdit={(r) => {
              setEditing(r);
              setMode("edit");
              setFormError(null);
            }}
            onChanged={() => routinesRes.refresh()}
            onDeleted={() => {
              setSelectedId(null);
              routinesRes.refresh();
            }}
          />
        </Card>
      );
    }
    return (
      <Card className="notice-card">
        <h3>No routine selected</h3>
        <p className="muted">Select a routine on the left, or create a new one.</p>
      </Card>
    );
  };

  return (
    <div className="view">
      <PageHeader
        icon="🔁"
        title="Routines"
        subtitle="Put your OpenClaw agents to work on a schedule — daily reports, follow-ups, and recurring company tasks. Runs while Evano is open."
        badge={<Badge tone="alpha">Live</Badge>}
      />

      <div className="toolbar">
        <span className="muted">
          {routinesRes.state === "ready" ? `${routines.length} routine(s)` : "—"}
        </span>
        <div className="toolbar-actions">
          <Button onClick={() => routinesRes.refresh()}>↻ Refresh</Button>
          <Button
            variant="primary"
            onClick={() => {
              setEditing(null);
              setMode("create");
              setFormError(null);
            }}
          >
            + New Routine
          </Button>
        </div>
      </div>

      <div className="agents-layout">
        <aside className="agents-sidebar">{renderList()}</aside>
        <section className="agents-detail">{renderDetail()}</section>
      </div>
    </div>
  );
}
