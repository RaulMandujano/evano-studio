/** One desk in the office — occupied (agent working) or empty (agent on break). */
import type { OfficeWorker } from "../../lib/office";
import { KIND_META } from "../../lib/office";

export function Desk({ worker }: { worker: OfficeWorker }) {
  const working = worker.working;

  return (
    <div className={`office-desk ${working ? "office-desk--busy" : ""}`} title={working?.task}>
      {working ? (
        <div className="desk-bubble">
          <span className="desk-bubble-kind">{KIND_META[working.kind].icon}</span>
          <span className="desk-bubble-task">{working.task}</span>
        </div>
      ) : null}

      <div className="desk-monitor">
        <div className="desk-screen">
          {working ? (
            <span className="desk-typing">
              <i />
              <i />
              <i />
            </span>
          ) : null}
        </div>
        <div className="desk-stand" />
      </div>

      <div className="desk-surface" />

      <div className="desk-seat">
        {working ? <span className="desk-worker">{worker.avatar}</span> : <span className="desk-chair" />}
      </div>

      <div className="desk-label">
        <span className={`office-dot ${working ? "office-dot--busy" : "office-dot--idle"}`} />
        {worker.name}
      </div>
    </div>
  );
}
