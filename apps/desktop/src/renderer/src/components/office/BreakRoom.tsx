/** The break room — where idle agents hang out and disabled agents nap. */
import type { OfficeWorker } from "../../lib/office";

export function BreakRoom({ idle, offDuty }: { idle: OfficeWorker[]; offDuty: OfficeWorker[] }) {
  const empty = idle.length === 0 && offDuty.length === 0;

  return (
    <div className="office-zone office-zone--break">
      <div className="office-zone-head">
        <h3>☕ Break room</h3>
        <p className="muted">
          {empty ? "Empty — everyone is working!" : "Agents waiting for their next task."}
        </p>
      </div>
      <div className="break-floor">
        {idle.map((w) => (
          <div key={w.key} className="break-worker" title={`${w.name} — idle, ready to work`}>
            <span className="break-steam">
              <i>~</i>
              <i>~</i>
            </span>
            <span className="break-avatar">{w.avatar}</span>
            <span className="break-prop">☕</span>
            <span className="break-name">{w.name}</span>
          </div>
        ))}
        {offDuty.map((w) => (
          <div key={w.key} className="break-worker break-worker--off" title={`${w.name} — disabled (off duty)`}>
            <span className="break-zzz">z z z</span>
            <span className="break-avatar">😴</span>
            <span className="break-name">{w.name}</span>
          </div>
        ))}
        {empty ? <span className="break-empty">🪴</span> : null}
      </div>
    </div>
  );
}
