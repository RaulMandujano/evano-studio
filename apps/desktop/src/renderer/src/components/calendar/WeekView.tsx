import { formatTime, isSameDay, weekDays } from "../../lib/calendar";
import type { CalendarEvent } from "../../lib/api/types";

interface WeekViewProps {
  weekDate: Date;
  events: CalendarEvent[];
  onSelectEvent: (event: CalendarEvent) => void;
}

export function WeekView({ weekDate, events, onSelectEvent }: WeekViewProps) {
  const days = weekDays(weekDate);
  const today = new Date();

  return (
    <div className="week">
      {days.map((day) => {
        const dayEvents = events
          .filter((e) => isSameDay(new Date(e.time), day))
          .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
        return (
          <div key={day.toISOString()} className="week-day">
            <div className={`week-day-head${isSameDay(day, today) ? " is-today" : ""}`}>
              {day.toLocaleDateString(undefined, { weekday: "short", day: "numeric" })}
            </div>
            <div className="week-day-events">
              {dayEvents.length === 0 ? (
                <span className="muted week-empty">—</span>
              ) : (
                dayEvents.map((event, i) => (
                  <button
                    key={i}
                    type="button"
                    className={`cal-event cal-event--${event.type}`}
                    onClick={() => onSelectEvent(event)}
                  >
                    <span className="cal-event-time">{formatTime(new Date(event.time))}</span>
                    <span className="cal-event-name">{event.routine_name}</span>
                  </button>
                ))
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
