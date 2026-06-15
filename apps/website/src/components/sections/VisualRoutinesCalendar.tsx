import { Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";

/** Dark product mockup: a month calendar with scheduled-routine event chips. */
function CalendarMockup() {
  // a few "days" carry an event chip; tone cycles success / scheduled / amber
  const events: Record<number, { tone: string; label: string }> = {
    3: { tone: "ok", label: "Daily prices" },
    8: { tone: "accent", label: "Weekly report" },
    12: { tone: "ok", label: "Daily prices" },
    17: { tone: "amber", label: "Newsletter" },
    21: { tone: "ok", label: "Daily prices" },
    25: { tone: "accent", label: "Weekly report" },
  };
  return (
    <div className="mockup mockup--sm" aria-hidden="true">
      <div className="mockup-bar">
        <span className="mockup-dot" />
        <span className="mockup-dot" />
        <span className="mockup-dot" />
        <span className="mockup-title">Evano Studio — Calendar · June</span>
      </div>
      <div className="mockup-main">
        <div className="mk-cal">
          {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
            <span key={i} className="mk-cal-dow">
              {d}
            </span>
          ))}
          {Array.from({ length: 28 }).map((_, i) => {
            const day = i + 1;
            const ev = events[day];
            return (
              <div key={day} className="mk-cal-cell">
                <span className="mk-cal-num">{day}</span>
                {ev ? <span className={`mk-cal-ev mk-cal-ev--${ev.tone}`}>{ev.label}</span> : null}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function VisualRoutinesCalendar() {
  return (
    <Section id="routines">
      <div className="split">
        <Reveal>
          <span className="eyebrow">Visual routines calendar</span>
          <h2 className="split-title">Schedule agents from a calendar</h2>
          <p className="split-text">
            Turn repeatable agent tasks into <strong>routines</strong> and manage
            them from a visual calendar. See what is scheduled, what ran, and
            what to expect next — in plain language, no cron syntax.
          </p>
          <ul className="check-list">
            <li className="check-item">
              <span className="tick">✓</span>
              <span>One-time, daily, weekly, and monthly schedules.</span>
            </li>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>Run history with clear success, failed, and missed states.</span>
            </li>
            <li className="check-item">
              <span className="tick">✓</span>
              <span>
                Routines run while the app is open — Evano Studio is not a
                background cloud service.
              </span>
            </li>
          </ul>
        </Reveal>
        <Reveal className="split-media reveal-d1" scale>
          <CalendarMockup />
        </Reveal>
      </div>
    </Section>
  );
}
