"""Run a saved team workflow on the backend (for autonomous / scheduled runs).

Mirrors the desktop relay: each agent does its task using the previous agent's
output as input, via OpenClaw's native one-shot agent. Used by the routine
scheduler so a whole workflow can run by itself with no person present.
"""

from __future__ import annotations

import logging

from .activity_service import track
from .openclaw_service import OpenClawService

logger = logging.getLogger("evano.agent_engine.routines")

_DIRECTIVE = (
    "\nIMPORTANT: Reply with ONLY the finished result of your task — the actual deliverable. "
    'Do NOT describe your plan, do NOT say "I will…", do NOT ask questions or add preamble. '
    "Just produce the result."
)


def _file_note(working_file: str | None, first: bool) -> str:
    if not working_file:
        return ""
    if first:
        return (
            f"\nUse your file tools to write your result into the file `{working_file}` "
            "in your workspace (create it)."
        )
    return (
        f"\nThe file `{working_file}` is already in your workspace (your teammate left it there). "
        f"Read it, do your task, and SAVE your changes back to `{working_file}` with your file tools."
    )


def _first_message(team: str, agent: str, instruction: str, started: str, working_file: str | None) -> str:
    parts = [
        f'You are "{agent}", one member of the team "{team}". The team completes a task as a relay.',
        f"Your task: {instruction}" if instruction else "Do your part of the team's work.",
    ]
    if started:
        parts.append(f"\nInput / goal to start from:\n{started}")
    parts.append(_file_note(working_file, first=True))
    parts.append(_DIRECTIVE)
    return "\n".join(p for p in parts if p)


def _handoff_message(
    team: str, agent: str, instruction: str, prev_name: str, prev_output: str, working_file: str | None
) -> str:
    parts = [
        f'You are "{agent}", one member of the team "{team}".',
        f"Your task: {instruction}" if instruction else "Continue the team's work.",
        f'\nYour teammate "{prev_name}" already did their part and gave you this result:\n---\n{prev_output}\n---',
        "\nDo YOUR task using their result above as your input.",
        _file_note(working_file, first=False),
        _DIRECTIVE,
    ]
    return "\n".join(p for p in parts if p)


def run_team(*, name: str, steps: list[dict], starting_input: str = "", working_file: str | None = None) -> dict:
    """Run a team's ordered steps. Returns {ok, final, error, steps:[...]}.

    When ``working_file`` is set, the file is copied from each agent's workspace to
    the next agent's before that agent runs, so a single file flows through the team.
    """
    svc = OpenClawService()
    results: list[dict] = []
    context = ""
    prev_name = ""

    if len([s for s in steps if s.get("agent_id")]) == 0:
        return {"ok": False, "final": "", "error": "Team has no agents.", "steps": []}

    for i, step in enumerate(steps):
        agent_id = (step.get("agent_id") or "").strip()
        instruction = step.get("instruction") or ""
        if not agent_id:
            continue
        # Hand the working file from the previous agent's folder to this one.
        if working_file and prev_name:
            svc.handoff_file(from_agent_id=prev_name, to_agent_id=agent_id, file_name=working_file)
        message = (
            _first_message(name, agent_id, instruction, starting_input, working_file)
            if i == 0
            else _handoff_message(name, agent_id, instruction, prev_name, context, working_file)
        )
        step_label = f'Team "{name}" — step {i + 1}/{len(steps)}: {instruction or "do their part"}'
        with track(agent_id=f"openclaw:{agent_id}", agent_name=agent_id, kind="team", task=step_label) as outcome:
            reply_data = svc.agent_chat(agent_id=agent_id, message=message)
            reply = (reply_data.get("reply") or "").strip()
            ok = bool(reply_data.get("ok")) and reply and reply != "(no reply)"
            outcome["ok"] = bool(ok)
            if not ok:
                outcome["note"] = reply_data.get("message") or f"{agent_id} returned no output."
        results.append({"agent_id": agent_id, "instruction": instruction, "ok": ok, "output": reply})
        if not ok:
            err = reply_data.get("message") or f"{agent_id} returned no output."
            logger.info("team run stopped at step=%s agent=%s: %s", i, agent_id, err)
            return {"ok": False, "final": "", "error": err, "steps": results}
        context = reply
        prev_name = agent_id

    return {"ok": True, "final": context, "error": None, "steps": results}
