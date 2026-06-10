/** Side panel: what's happening now + what just finished. */
import type { AgentActivity } from "../../lib/api/types";
import { KIND_META, timeAgo } from "../../lib/office";

const MAX_RECENT = 20;

function FeedRow({ activity }: { activity: AgentActivity }) {
  const meta = KIND_META[activity.kind] ?? { icon: "💬", label: activity.kind };
  const statusIcon = activity.status === "working" ? "⏳" : activity.status === "done" ? "✅" : "⚠️";
  const when = activity.status === "working" ? `started ${timeAgo(activity.started_at)}` : timeAgo(activity.finished_at);

  return (
    <li className={`feed-row feed-row--${activity.status}`}>
      <span className="feed-status">{statusIcon}</span>
      <div className="feed-body">
        <p className="feed-line">
          <strong>{activity.agent_name}</strong> <span className="feed-kind">{meta.icon} {meta.label}</span>
        </p>
        <p className="feed-task">{activity.task}</p>
        {activity.note ? <p className="feed-note">{activity.note}</p> : null}
        <p className="feed-when">{when}</p>
      </div>
    </li>
  );
}

export function ActivityFeed({ active, recent }: { active: AgentActivity[]; recent: AgentActivity[] }) {
  return (
    <aside className="office-feed">
      <h3 className="section-label">⏳ Working now</h3>
      {active.length === 0 ? (
        <p className="muted feed-quiet">Nobody right now — chat with an agent, run a team, or wait for a routine.</p>
      ) : (
        <ul className="feed-list">
          {active.map((a) => (
            <FeedRow key={a.id} activity={a} />
          ))}
        </ul>
      )}

      <h3 className="section-label">🗂️ Recent work</h3>
      {recent.length === 0 ? (
        <p className="muted feed-quiet">Finished work will show up here.</p>
      ) : (
        <ul className="feed-list">
          {recent.slice(0, MAX_RECENT).map((a) => (
            <FeedRow key={a.id} activity={a} />
          ))}
        </ul>
      )}
    </aside>
  );
}
