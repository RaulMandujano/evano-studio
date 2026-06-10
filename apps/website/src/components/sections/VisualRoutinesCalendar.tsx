import { Section } from "@/components/ui/Section";

export function VisualRoutinesCalendar() {
  return (
    <Section id="routines">
      <div className="split">
        <div>
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
        </div>
        <div className="split-media">
          <div className="panel" aria-hidden="true">
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(7, 1fr)",
                gap: 8,
              }}
            >
              {Array.from({ length: 28 }).map((_, i) => (
                <div
                  key={i}
                  style={{
                    aspectRatio: "1 / 1",
                    borderRadius: 8,
                    border: "1px solid var(--border)",
                    background:
                      i % 9 === 4
                        ? "var(--accent-soft)"
                        : i % 7 === 2
                          ? "var(--teal-soft)"
                          : "var(--surface-2)",
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
}
