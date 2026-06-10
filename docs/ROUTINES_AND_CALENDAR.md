# Routines & Calendar

Routines let an agent run a repeatable task on a schedule. The calendar is the visual way users view and manage those routines. This is a design document — **no code exists yet**.

---

## What are routines?

A **routine** is a saved instruction that runs a specific **agent task on a schedule**. For example: "Every Monday at 9am, have the Document Drafter create a weekly summary." A routine ties together:

- An **agent** (which model + permissions + tools to use — see [AGENTS.md](AGENTS.md)).
- A **task** (the instruction/prompt the agent should carry out).
- A **schedule** (when it should run).
- An **output target** (e.g., a document saved to the workspace).

Routines turn one-off agent work into dependable, recurring work — the "set it and forget it" value for small businesses.

---

## Supported schedule types for V1

V1 keeps scheduling simple and predictable:

- **One-time** — run once at a specific date and time.
- **Daily** — run every day at a chosen time.
- **Weekly** — run on chosen day(s) of the week at a chosen time.
- **Monthly** — run on a chosen day of the month at a chosen time.

Out of scope for V1 (may come later):

- ❌ Arbitrary cron expressions exposed to users.
- ❌ Sub-hourly / high-frequency schedules.
- ❌ Event-triggered routines (run when X happens).
- ❌ Complex dependencies between routines.

Schedules use the user's **local timezone**.

---

## Visual calendar requirements

The calendar is the primary UI for routines.

- **Month view** at minimum; week view is desirable.
- Shows **scheduled routine runs** as calendar entries.
- Shows **past runs with their status** (success, failed, missed).
- Clicking an entry shows details: which agent, the task, the schedule, last result, and a link to the output/log.
- Create / edit / delete / pause a routine directly from the calendar.
- Clear visual distinction between **upcoming**, **completed**, **failed**, and **missed** runs.
- Designed for **non-technical users** — plain language, no cron syntax.

---

## Routine execution rules

- The **scheduler runs inside the local backend** (`routine_runner`, see [ARCHITECTURE.md](ARCHITECTURE.md)).
- When a routine is due **and the app is running**, the runner executes the agent task using that agent's configured model, permissions, and tools.
- **Permissions are enforced the same way as interactive use** — a routine cannot do anything its agent isn't allowed to do (see [SECURITY.md](SECURITY.md)).
- Each run produces a **run record** (start time, end time, status, output reference) stored in SQLite.
- Runs are **not retried automatically** in V1 unless the schedule itself comes due again. (No silent retry storms.)
- A routine can be **paused**; paused routines don't run until resumed.
- Outputs go to the agent's approved workspace scope — never outside it.

---

## What happens if the backend is closed

This is a **local-first app, not a background daemon** in V1. So:

- **If the app (and its backend) is closed when a routine is due, the routine does not run.** Evano Studio does not run in the background after you quit.
- When the app is reopened, any routine runs that were due while it was closed are recorded as **"missed"** in the run history and shown on the calendar.
- **Missed runs are not silently auto-executed on launch.** The user can see what was missed and choose to run it manually if they want.
- This behavior is communicated honestly in the UI and docs so users understand routines depend on the app being open.

> A true always-on background scheduler is explicitly out of scope for V1 (see [ROADMAP.md](ROADMAP.md)). It may be considered later, with appropriate user consent and OS integration.

---

## Logging requirements

- **Every routine run is logged**: when it started, the agent used, success/failure/missed, and a reference to its output.
- Logs are stored locally (`data/logs`) and surfaced in the routine/calendar UI and the general logs view.
- Logs **must not contain secrets or private content** beyond what's needed to understand the run (see [SECURITY.md](SECURITY.md)). The support bundle excludes private contents by default.
- Failures log enough context for the user to understand and act (e.g., "model not available", "ComfyUI not configured") in plain language.
