import { useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { MonthView } from "../components/calendar/MonthView";
import { WeekView } from "../components/calendar/WeekView";
import { RoutineForm } from "../components/routines/RoutineForm";
import { RoutineDetailPanel } from "../components/routines/RoutineDetailPanel";
import { useBackendResource } from "../hooks/useBackendResource";
import { backendApi } from "../lib/api/client";
import { addMonths, addWeeks, formatMonthYear, formatWeekRange } from "../lib/calendar";
import type {
  CalendarEvent,
  CalendarEventsResponse,
  OpenClawAgentsResponse,
  Routine,
  RoutineCreate,
} from "../lib/api/types";

type ViewMode = "month" | "week";
type PanelMode = "idle" | "create" | "edit";

export function CalendarView() {
  const eventsRes = useBackendResource<CalendarEventsResponse>(backendApi.getCalendarEvents);
  const agentsRes = useBackendResource<OpenClawAgentsResponse>(backendApi.getOpenClawAgents);

  const [cursor, setCursor] = useState<Date>(() => new Date());
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [panelMode, setPanelMode] = useState<PanelMode>("idle");
  const [selectedRoutineId, setSelectedRoutineId] = useState<number | null>(null);
  const [editing, setEditing] = useState<Routine | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const agents = agentsRes.data?.agents ?? [];
  const events = eventsRes.data?.events ?? [];

  const goBack = () => setCursor((c) => (viewMode === "month" ? addMonths(c, -1) : addWeeks(c, -1)));
  const goForward = () => setCursor((c) => (viewMode === "month" ? addMonths(c, 1) : addWeeks(c, 1)));
  const goToday = () => setCursor(new Date());

  const onSelectEvent = (event: CalendarEvent) => {
    setSelectedRoutineId(event.routine_id);
    setPanelMode("idle");
  };

  const submit = async (data: RoutineCreate, id?: number) => {
    setSubmitting(true);
    setFormError(null);
    try {
      const saved = id
        ? await backendApi.updateRoutine(id, data)
        : await backendApi.createRoutine(data);
      eventsRes.refresh();
      setSelectedRoutineId(saved.id);
      setPanelMode("idle");
    } catch (e) {
      setFormError(e instanceof Error ? e.message : "Couldn't save the routine.");
    } finally {
      setSubmitting(false);
    }
  };

  const renderCalendar = () => {
    if (eventsRes.state === "checking") {
      return <p className="muted">Loading calendar…</p>;
    }
    if (eventsRes.state !== "ready") {
      return (
        <Card className="notice-card">
          <h3>Can&apos;t reach the local backend</h3>
          <p className="muted">Start the Agent Engine, then refresh.</p>
        </Card>
      );
    }
    if (viewMode === "month") {
      return <MonthView monthDate={cursor} events={events} onSelectEvent={onSelectEvent} />;
    }
    return <WeekView weekDate={cursor} events={events} onSelectEvent={onSelectEvent} />;
  };

  const renderPanel = () => {
    if (panelMode === "create" || panelMode === "edit") {
      return (
        <Card>
          <RoutineForm
            initial={panelMode === "edit" ? editing : null}
            agents={agents}
            submitting={submitting}
            error={formError}
            onSubmit={(data) => submit(data, panelMode === "edit" ? editing?.id : undefined)}
            onCancel={() => setPanelMode("idle")}
          />
        </Card>
      );
    }
    if (selectedRoutineId !== null) {
      return (
        <Card>
          <RoutineDetailPanel
            routineId={selectedRoutineId}
            agents={agents}
            onEdit={(r) => {
              setEditing(r);
              setPanelMode("edit");
              setFormError(null);
            }}
            onChanged={() => eventsRes.refresh()}
            onDeleted={() => {
              setSelectedRoutineId(null);
              eventsRes.refresh();
            }}
          />
        </Card>
      );
    }
    return (
      <Card className="notice-card">
        <h3>Routine details</h3>
        <p className="muted">Click an event to view a routine, or create a new one.</p>
      </Card>
    );
  };

  return (
    <div className="view view--wide">
      <PageHeader
        icon="🗓️"
        title="Calendar"
        subtitle="See and manage your scheduled routines. Local only — no cloud calendar."
        badge={<Badge tone="alpha">Live</Badge>}
      />

      <div className="cal-toolbar">
        <div className="cal-nav">
          <Button onClick={goBack}>◀</Button>
          <Button onClick={goToday}>Today</Button>
          <Button onClick={goForward}>▶</Button>
          <span className="cal-title">
            {viewMode === "month" ? formatMonthYear(cursor) : formatWeekRange(cursor)}
          </span>
        </div>
        <div className="cal-toolbar-actions">
          <div className="cal-modeswitch">
            <button
              type="button"
              className={`cal-mode${viewMode === "month" ? " is-active" : ""}`}
              onClick={() => setViewMode("month")}
            >
              Month
            </button>
            <button
              type="button"
              className={`cal-mode${viewMode === "week" ? " is-active" : ""}`}
              onClick={() => setViewMode("week")}
            >
              Week
            </button>
          </div>
          <Button onClick={() => eventsRes.refresh()}>↻</Button>
          <Button
            variant="primary"
            onClick={() => {
              setEditing(null);
              setPanelMode("create");
              setFormError(null);
            }}
          >
            + New Routine
          </Button>
        </div>
      </div>

      <div className="calendar-layout">
        <section className="calendar-main">{renderCalendar()}</section>
        <aside className="calendar-panel">{renderPanel()}</aside>
      </div>
    </div>
  );
}
