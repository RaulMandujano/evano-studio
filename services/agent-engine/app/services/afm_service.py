"""AFM — Agent File Management.

One tidy, user-chosen folder for everything agents create:

    <root>/
      Agents/<Agent Name>/      ← the agent's REAL OpenClaw workspace
      Teams/<Team Name>/        ← team run results
        <Member Name>/          ← each member's step outputs

Instead of copying files around, AFM points each OpenClaw agent's workspace at
its folder (agents.list[].workspace in openclaw.json) and moves the existing
content there — so every prompt, report, or image an agent writes lands in the
user's structure organically. The root defaults to the Evano workspace folder;
the user can pick any folder instead.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from ..core.config import Settings
from ..core.workspace import effective_workspace, validate_workspace_path
from ..db.models import AppSetting, Team
from .openclaw_service import OpenClawService
from .openclaw_service import config as oc_config

logger = logging.getLogger("evano.agent_engine.afm")

AFM_ROOT_KEY = "afm_root"  # AppSetting; "" = use the default (Evano workspace)
AGENTS_DIR = "Agents"
TEAMS_DIR = "Teams"


def _safe_name(name: str) -> str:
    """A filesystem-friendly folder name that still reads like the agent/team."""
    cleaned = re.sub(r"[^A-Za-z0-9 _-]+", "", (name or "").strip()).strip()
    return cleaned[:60] or "Unnamed"


class AFMService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._oc = OpenClawService()

    # ---- root resolution -------------------------------------------------- #

    def default_root(self) -> Path:
        return effective_workspace(self._session, self._settings)

    def configured_root(self) -> tuple[Path, bool]:
        """(root, is_default). The AppSetting stores "" for the default."""
        row = self._session.get(AppSetting, AFM_ROOT_KEY)
        if row is not None and row.value.strip():
            return Path(row.value.strip()).expanduser(), False
        return self.default_root(), True

    def is_configured(self) -> bool:
        return self._session.get(AppSetting, AFM_ROOT_KEY) is not None

    def agent_target_dir(self, agent_name: str) -> Path:
        root, _ = self.configured_root()
        return root / AGENTS_DIR / _safe_name(agent_name)

    # ---- status ------------------------------------------------------------ #

    def status(self) -> dict:
        root, is_default = self.configured_root()
        agents_res = self._oc.list_agents()
        identities = self._oc._config_identities()
        agents = []
        for a in agents_res.get("agents") or []:
            ident = identities.get(a["id"], {})
            name = ident.get("name") or a.get("name") or a["id"]
            target = root / AGENTS_DIR / _safe_name(name)
            workspace = a.get("workspace") or ""
            managed = False
            try:
                managed = bool(workspace) and Path(workspace).resolve() == target.resolve()
            except OSError:
                managed = False
            agents.append({
                "agent_id": a["id"],
                "name": name,
                "emoji": ident.get("emoji") or "",
                "workspace": workspace,
                "target": str(target),
                "managed": managed,
            })
        teams = []
        for team in self._session.exec(select(Team)).all():
            folder = root / TEAMS_DIR / _safe_name(team.name)
            members = []
            for step in team.steps or []:
                aid = (step.get("agent_id") or "").strip()
                if not aid:
                    continue
                ident = identities.get(aid, {})
                member = ident.get("name") or aid
                if member not in members:
                    members.append(member)
            teams.append({
                "team_id": team.id,
                "name": team.name,
                "folder": str(folder),
                "exists": folder.is_dir(),
                "members": members,
            })
        return {
            "ok": bool(agents_res.get("ok")),
            "message": agents_res.get("message") or "",
            "root": str(root),
            "is_default": is_default,
            "configured": self.is_configured(),
            "agents": agents,
            "teams": teams,
        }

    # ---- apply -------------------------------------------------------------- #

    def apply(self, root_path: str | None) -> dict:
        """Choose the root and organize: move every agent's workspace into
        <root>/Agents/<Name>, update OpenClaw's config, and scaffold team folders."""
        if root_path and root_path.strip():
            root = validate_workspace_path(root_path)
            stored = str(root)
        else:
            root = self.default_root()
            stored = ""  # default marker — follows the Evano workspace setting

        agents_res = self._oc.list_agents()
        if not agents_res.get("ok"):
            return {"ok": False, "message": agents_res.get("message") or "OpenClaw isn't ready.",
                    "moved": [], "skipped": []}

        try:
            (root / AGENTS_DIR).mkdir(parents=True, exist_ok=True)
            (root / TEAMS_DIR).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return {"ok": False, "message": f"Couldn't create the AFM folders: {exc}", "moved": [], "skipped": []}

        # Persist the choice first so new agents are created inside the root.
        row = self._session.get(AppSetting, AFM_ROOT_KEY)
        if row is None:
            self._session.add(AppSetting(key=AFM_ROOT_KEY, value=stored))
        else:
            row.value = stored
            self._session.add(row)
        self._session.commit()

        identities = self._oc._config_identities()
        gateway_was_running = self._gateway_running()
        if gateway_was_running:
            self._oc.gateway_stop()

        moved: list[str] = []
        skipped: list[str] = []
        new_paths: dict[str, str] = {}
        for a in agents_res.get("agents") or []:
            aid = a["id"]
            ident = identities.get(aid, {})
            name = ident.get("name") or a.get("name") or aid
            target = root / AGENTS_DIR / _safe_name(name)
            current = Path(a["workspace"]).expanduser() if a.get("workspace") else None
            try:
                if current and current.resolve() == target.resolve():
                    new_paths[aid] = str(target)
                    continue  # already in place
                if target.exists() and any(target.iterdir()):
                    skipped.append(f"{name} (folder already exists at {target})")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if current and current.is_dir():
                    shutil.move(str(current), str(target))
                else:
                    target.mkdir(parents=True, exist_ok=True)
                new_paths[aid] = str(target)
                moved.append(name)
            except OSError as exc:
                skipped.append(f"{name} ({exc})")

        config_ok = self._update_config_workspaces(new_paths)
        # Workspaces moved — the cached roster is stale now.
        from .openclaw_service._agents import invalidate_agents_cache

        invalidate_agents_cache()
        if gateway_was_running:
            self._oc.gateway_start()

        self._scaffold_team_folders(root, identities)

        if not config_ok:
            return {"ok": False, "message": "Files were organized but OpenClaw's config couldn't be updated.",
                    "moved": moved, "skipped": skipped}
        message = f"AFM active at {root}."
        if moved:
            message += f" Moved {len(moved)} agent folder(s)."
        if skipped:
            message += f" Skipped: {'; '.join(skipped)}."
        logger.info("afm apply root=%s moved=%d skipped=%d", root, len(moved), len(skipped))
        return {"ok": True, "message": message, "moved": moved, "skipped": skipped}

    # ---- team run archiving -------------------------------------------------- #

    def archive_team_run(self, *, team_name: str, steps: list[dict], final: str) -> dict:
        """Save a finished team run into <root>/Teams/<Team>/: each member's step
        output in their subfolder, the final result at the team folder root."""
        root, _ = self.configured_root()
        identities = self._oc._config_identities()
        folder = root / TEAMS_DIR / _safe_name(team_name)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        try:
            folder.mkdir(parents=True, exist_ok=True)
            for i, step in enumerate(steps):
                output = (step.get("output") or "").strip()
                if not output:
                    continue
                aid = (step.get("agent_id") or "").strip() or f"step-{i + 1}"
                member = identities.get(aid, {}).get("name") or aid
                member_dir = folder / _safe_name(member)
                member_dir.mkdir(parents=True, exist_ok=True)
                (member_dir / f"run-{stamp}-step{i + 1}.md").write_text(output + "\n", encoding="utf-8")
            if (final or "").strip():
                (folder / f"final-{stamp}.md").write_text(final.strip() + "\n", encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "folder": str(folder), "message": f"Couldn't save the run: {exc}"}
        logger.info("afm team run archived team=%s steps=%d", team_name, len(steps))
        return {"ok": True, "folder": str(folder), "message": f"Run saved to {folder}."}

    # ---- helpers --------------------------------------------------------------- #

    def _gateway_running(self) -> bool:
        from .openclaw_service import process as oc_process

        return oc_process._port_open(self._oc._gateway_port())

    def _update_config_workspaces(self, new_paths: dict[str, str]) -> bool:
        cfg_file = oc_config.CONFIG_FILE
        if not cfg_file.exists() or not new_paths:
            return cfg_file.exists()
        try:
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return False
        agents_cfg = cfg.setdefault("agents", {})
        entries = agents_cfg.setdefault("list", [])
        seen = set()
        for entry in entries:
            aid = entry.get("id")
            if aid in new_paths:
                entry["workspace"] = new_paths[aid]
                seen.add(aid)
        for aid, ws in new_paths.items():
            if aid not in seen:
                entries.append({"id": aid, "workspace": ws})
        try:
            tmp = cfg_file.with_name(cfg_file.name + ".tmp")
            tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            tmp.replace(cfg_file)
        except OSError:
            return False
        return True

    def _scaffold_team_folders(self, root: Path, identities: dict[str, dict]) -> None:
        try:
            for team in self._session.exec(select(Team)).all():
                folder = root / TEAMS_DIR / _safe_name(team.name)
                folder.mkdir(parents=True, exist_ok=True)
                for step in team.steps or []:
                    aid = (step.get("agent_id") or "").strip()
                    if not aid:
                        continue
                    member = identities.get(aid, {}).get("name") or aid
                    (folder / _safe_name(member)).mkdir(exist_ok=True)
        except OSError:
            pass  # cosmetic scaffolding — never fail apply for this
