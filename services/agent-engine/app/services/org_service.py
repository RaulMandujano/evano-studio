"""Org chart service — who manages whom, applied to OpenClaw as REAL permissions.

The chart is a tree of OpenClaw agents (one manager per agent, no cycles).
Saving it does three things, so it's never just a drawing:

1. ``subagents.allowAgents`` in openclaw.json — each manager may delegate ONLY
   to its direct reports (OpenClaw's native ``sessions_spawn`` allowlist,
   deny-by-default like everything in Evano).
2. A managed block in each manager's AGENTS.md — the agent learns who is on its
   team and how to delegate (results announce back to the requester channel, so
   delegation works from Discord too).
3. ``agents.defaults.subagents.maxSpawnDepth`` — raised to the real tree depth
   (capped at 3) so multi-level hierarchies work without runaway nesting.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlmodel import Session, select

from ..core.errors import AppError
from ..db.models import OrgLink
from .openclaw_service import OpenClawService
from .openclaw_service import config as oc_config

logger = logging.getLogger("evano.agent_engine.org")

ORG_BLOCK_START = "<!-- EVANO-ORG:START — managed by Evano Studio Org Chart; edited automatically -->"
ORG_BLOCK_END = "<!-- EVANO-ORG:END -->"

_MAX_SPAWN_DEPTH_CAP = 3


def _delegation_block(reports: list[dict]) -> str:
    lines = [
        ORG_BLOCK_START,
        "",
        "## Your team (Org Chart)",
        "",
        "You are a manager. Your direct reports:",
        "",
    ]
    for r in reports:
        emoji = f"{r['emoji']} " if r.get("emoji") else ""
        lines.append(f"- {emoji}**{r['name']}** — delegate with `agentId: \"{r['id']}\"`")
    lines += [
        "",
        "How to delegate:",
        "",
        "- Use the `sessions_spawn` tool with the report's `agentId` and a clear,",
        "  self-contained task (they can't see this conversation).",
        "- Split independent subtasks across teammates in parallel; do quick things yourself.",
        "- After spawning, call `sessions_yield` to wait — results are announced back",
        "  to this conversation automatically.",
        "- Combine your team's results into one final answer for the user.",
        "- You can only delegate to the agents listed above.",
        "",
        ORG_BLOCK_END,
    ]
    return "\n".join(lines)


def _strip_block(text: str) -> str:
    start = text.find(ORG_BLOCK_START)
    end = text.find(ORG_BLOCK_END)
    if start == -1 or end == -1 or end < start:
        return text
    return (text[:start].rstrip() + "\n" + text[end + len(ORG_BLOCK_END):].lstrip("\n")).strip() + "\n"


class OrgService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._oc = OpenClawService()

    # ---- read ------------------------------------------------------------ #

    def get_chart(self) -> dict:
        agents_res = self._oc.list_agents()
        identities = self._identities()
        agents = []
        for a in agents_res.get("agents") or []:
            ident = identities.get(a["id"], {})
            agents.append({
                "id": a["id"],
                "name": ident.get("name") or a.get("name") or a["id"],
                "emoji": ident.get("emoji") or "",
                "model": a.get("model") or "",
                "workspace": a.get("workspace") or "",
                "is_default": bool(a.get("is_default")),
            })
        links = [
            {"agent_id": l.agent_id, "parent_agent_id": l.parent_agent_id}
            for l in self._links()
        ]
        return {
            "ok": bool(agents_res.get("ok")),
            "message": agents_res.get("message") or "",
            "agents": agents,
            "links": links,
        }

    def _links(self) -> list[OrgLink]:
        return list(self._session.exec(select(OrgLink)).all())

    # ---- save + apply ----------------------------------------------------- #

    def save_chart(self, links: list[dict]) -> dict:
        agents_res = self._oc.list_agents()
        if not agents_res.get("ok"):
            return {"ok": False, "message": agents_res.get("message") or "OpenClaw isn't ready."}
        agents = agents_res.get("agents") or []
        ids = {a["id"] for a in agents}

        parent_of = self._validate(links, ids)

        # Replace the stored chart (flush deletes first — same ids may be re-inserted).
        for row in self._links():
            self._session.delete(row)
        self._session.flush()
        for child, parent in parent_of.items():
            self._session.add(OrgLink(agent_id=child, parent_agent_id=parent))
        self._session.commit()

        applied = self._apply(parent_of, agents)
        logger.info("org chart saved: %s reporting lines, applied=%s", len(parent_of), applied["ok"])
        return applied

    def _validate(self, links: list[dict], ids: set[str]) -> dict[str, str]:
        parent_of: dict[str, str] = {}
        for link in links:
            child = (link.get("agent_id") or "").strip()
            parent = (link.get("parent_agent_id") or "").strip()
            if not child or not parent:
                continue  # "no manager" rows are simply omitted
            if child not in ids:
                raise AppError(f"Unknown agent: {child}", status_code=400, code="invalid_org")
            if parent not in ids:
                raise AppError(f"Unknown manager: {parent}", status_code=400, code="invalid_org")
            if child == parent:
                raise AppError(f"{child} can't report to itself.", status_code=400, code="invalid_org")
            if child in parent_of:
                raise AppError(f"{child} has two managers — pick one.", status_code=400, code="invalid_org")
            parent_of[child] = parent
        # No cycles: walking up from any agent must terminate.
        for start in parent_of:
            seen = {start}
            node = parent_of[start]
            while node in parent_of:
                if node in seen:
                    raise AppError(
                        "That would create a loop (an agent managing its own manager). Fix the chain.",
                        status_code=400,
                        code="invalid_org",
                    )
                seen.add(node)
                node = parent_of[node]
        return parent_of

    def _apply(self, parent_of: dict[str, str], agents: list[dict]) -> dict:
        children: dict[str, list[str]] = {}
        for child, parent in parent_of.items():
            children.setdefault(parent, []).append(child)

        config_ok = self._apply_config(children, parent_of)
        identities = self._identities()
        notes_ok = self._apply_agent_notes(children, agents, identities)
        restarted = self._oc._restart_gateway_if_running()

        if not config_ok:
            return {"ok": False, "message": "Couldn't update OpenClaw's config — is it installed and configured?"}
        message = "Org chart applied — managers can now delegate to their teams."
        if restarted:
            message += " Gateway reloaded."
        if not notes_ok:
            message += " (Some team notes couldn't be written.)"
        return {"ok": True, "message": message}

    def _apply_config(self, children: dict[str, list[str]], parent_of: dict[str, str]) -> bool:
        """Write allowAgents per manager + maxSpawnDepth into openclaw.json."""
        cfg_file = oc_config.CONFIG_FILE
        if not cfg_file.exists():
            return False
        try:
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return False
        agents_cfg = cfg.setdefault("agents", {})
        for entry in agents_cfg.setdefault("list", []):
            aid = entry.get("id")
            if not aid:
                continue
            if aid in children:
                entry.setdefault("subagents", {})["allowAgents"] = sorted(children[aid])
            elif isinstance(entry.get("subagents"), dict):
                # No longer a manager — withdraw the delegation permission.
                entry["subagents"].pop("allowAgents", None)
                if not entry["subagents"]:
                    entry.pop("subagents")
        depth = self._tree_depth(parent_of)
        if depth >= 2:
            agents_cfg.setdefault("defaults", {}).setdefault("subagents", {})["maxSpawnDepth"] = min(
                depth, _MAX_SPAWN_DEPTH_CAP
            )
        try:
            tmp = cfg_file.with_name(cfg_file.name + ".tmp")
            tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            tmp.replace(cfg_file)
        except OSError:
            return False
        return True

    def _apply_agent_notes(
        self, children: dict[str, list[str]], agents: list[dict], identities: dict[str, dict]
    ) -> bool:
        """Maintain the managed "Your team" block in every agent's AGENTS.md."""
        all_ok = True
        for agent in agents:
            ws = agent.get("workspace")
            if not ws:
                continue
            path = Path(ws) / "AGENTS.md"
            try:
                text = path.read_text(encoding="utf-8") if path.is_file() else ""
                text = _strip_block(text)
                reports = children.get(agent["id"])
                if reports:
                    roster = []
                    for rid in sorted(reports):
                        ident = identities.get(rid, {})
                        roster.append({
                            "id": rid,
                            "name": ident.get("name") or rid,
                            "emoji": ident.get("emoji") or "",
                        })
                    text = text.rstrip() + "\n\n" + _delegation_block(roster) + "\n"
                if text.strip():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text, encoding="utf-8")
            except OSError:
                all_ok = False
        return all_ok

    @staticmethod
    def _tree_depth(parent_of: dict[str, str]) -> int:
        """Longest chain of command (1 = a manager with direct reports)."""
        depth = 0
        for start in parent_of:
            steps, node = 0, start
            while node in parent_of:
                steps += 1
                node = parent_of[node]
            depth = max(depth, steps)
        return depth

    def _identities(self) -> dict[str, dict]:
        """Friendly name/emoji per agent id, straight from openclaw.json."""
        try:
            cfg = json.loads(oc_config.CONFIG_FILE.read_text(encoding="utf-8")) if oc_config.CONFIG_FILE.exists() else {}
        except Exception:  # noqa: BLE001
            return {}
        out: dict[str, dict] = {}
        for entry in ((cfg.get("agents") or {}).get("list")) or []:
            ident = entry.get("identity") or {}
            out[entry.get("id", "")] = {
                "name": ident.get("name") or entry.get("name") or entry.get("id"),
                "emoji": ident.get("emoji") or "",
            }
        return out
