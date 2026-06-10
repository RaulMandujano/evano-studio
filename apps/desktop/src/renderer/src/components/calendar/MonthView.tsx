import {
  WEEKDAYS,
  formatTime,
  getMonthMatrix,
  isSameDay,
  isSameMonth,
} from "../../lib/calendar";
import type { CalendarEvent } from "../../lib/api/types";

interface MonthViewProps {
  monthDate: Date;
  events: CalendarEvent[];
  onSelectEvent: (event: CalendarEvent) => void;
}

function eventsForDay(events: CalendarEvent[], day: Date): CalendarEvent[] {
  return events
    .filter((e) => isSameDay(new Date(e.time), day))
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
}

export function MonthView({ monthDate, events, onSelectEvent }: MonthViewProps) {
  const weeks = getMonthMatrix(monthDate);
  const today = new Date();

  return (
    <div className="cal">
      <div className="cal-weekdays">
        {WEEKDAYS.map((d) => (
          <div key={d} className="cal-weekday">
            {d}
          </div>
        ))}
      </div>
      <div className="cal-grid">
        {weeks.map((week, wi) => (
          <div key={wi} className="cal-week">
            {week.map((day) => {
              const dayEvents = eventsForDay(events, day);
              const classes = ["cal-cell"];
              if (!isSameMonth(day, monthDate)) classes.push("cal-cell--dim");
              if (isSameDay(day, today)) classes.push("cal-cell--today");
              return (
                <div key={day.toISOString()} className={classes.join(" ")}>
                  <span className="cal-daynum">{day.getDate()}</span>
                  <div className="cal-events">
                    {dayEvents.map((event, i) => (
                      <button
                        key={i}
                        type="button"
                        className={`cal-event cal-event--${event.type}`}
                        title={`${event.routine_name} — ${event.status}`}
                        onClick={() => onSelectEvent(event)}
                      >
                        <span className="cal-event-time">{formatTime(new Date(event.time))}</span>
                        <span className="cal-event-name">{event.routine_name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
