"""Agents mixin: create/list/delete OpenClaw agents, chat, history, files."""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path

from . import config, metadata, process

logger = logging.getLogger("evano.agent_engine.openclaw")

# The OpenClaw CLI takes ~2s to boot Node for every call, and nearly every tab
# needs the agent roster. Cache the parsed list briefly; anything that changes
# the roster (create/delete, AFM moves) calls invalidate_agents_cache().
_AGENTS_CACHE_TTL = 15.0
_agents_cache: dict = {"at": 0.0, "data": None}
_agents_cache_lock = threading.Lock()


def invalidate_agents_cache() -> None:
    with _agents_cache_lock:
        _agents_cache["at"] = 0.0
        _agents_cache["data"] = None


class AgentsMixin:
    def list_agents(self) -> dict:
        with _agents_cache_lock:
            fresh = _agents_cache["data"] is not None and (time.monotonic() - _agents_cache["at"]) < _AGENTS_CACHE_TTL
            if fresh:
                cached = _agents_cache["data"]
                return {**cached, "agents": list(cached["agents"])}
        result = self._list_agents_uncached()
        if result.get("ok"):
            with _agents_cache_lock:
                _agents_cache["at"] = time.monotonic()
                _agents_cache["data"] = result
        return {**result, "agents": list(result["agents"])}

    def _list_agents_uncached(self) -> dict:
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first.", "agents": []}
        code, out, err = process._run(["openclaw", "agents", "list", "--json"], timeout=30)
        if code != 0:
            return {"ok": False, "message": (err or out or "Couldn't list agents.")[-300:], "agents": []}
        try:
            data = json.loads(out)
        except Exception:  # noqa: BLE001
            return {"ok": False, "message": "Couldn't read the agent list.", "agents": []}
        agents = []
        for a in data if isinstance(data, list) else []:
            agents.append({
                "id": a.get("id", ""),
                "name": a.get("id", ""),
                "model": a.get("model", ""),
                "workspace": a.get("workspace", ""),
                "is_default": bool(a.get("isDefault")),
                "bindings": int(a.get("bindings") or 0),
            })
        return {"ok": True, "message": "", "agents": agents}

    def create_agent(
        self, *, name: str, model: str | None, instructions: str | None, emoji: str | None,
        workspace: str | None = None,
    ) -> dict:
        """Create an isolated OpenClaw agent (its own workspace + model). The
        user's instructions are appended to the scaffolded AGENTS.md so the agent
        follows them; identity (name/emoji) is registered via set-identity.
        ``workspace`` overrides the default location (used by AFM)."""
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first.", "agent": None}
        slug = process._slugify(name)
        if not slug:
            return {"ok": False, "message": "Give the agent a name.", "agent": None}
        if slug == "main":
            return {"ok": False, "message": "That name is reserved — pick another.", "agent": None}
        ws = Path(workspace).expanduser() if workspace else config.CONFIG_DIR / "workspaces" / slug
        model = (model or "").strip() or "ollama/gemma4:latest"
        try:
            ws.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return {"ok": False, "message": f"Couldn't create the agent workspace: {exc}", "agent": None}

        code, out, err = process._run(
            ["openclaw", "agents", "add", slug, "--non-interactive",
             "--workspace", str(ws), "--model", model, "--json"],
            timeout=60,
        )
        if code != 0:
            return {"ok": False, "message": (err or out or "Couldn't create the agent.")[-400:], "agent": None}

        # Append the mission to the scaffolded AGENTS.md (never overwrite it).
        if instructions and instructions.strip():
            try:
                with (ws / "AGENTS.md").open("a", encoding="utf-8") as fh:
                    fh.write(f"\n\n## Mission (configured in Evano Studio)\n\n{instructions.strip()}\n")
            except OSError:
                pass  # non-fatal

        # Friendly name + emoji (best-effort; agent still works without it).
        ident = ["openclaw", "agents", "set-identity", "--agent", slug,
                 "--workspace", str(ws), "--name", name.strip()]
        if emoji and emoji.strip():
            ident += ["--emoji", emoji.strip()]
        ident += ["--json"]
        process._run(ident, timeout=30)

        invalidate_agents_cache()
        logger.info("openclaw agents add id=%s model=%s ok=True", slug, model)
        return {
            "ok": True,
            "message": "Agent created.",
            "agent": {"id": slug, "name": name.strip(), "model": model,
                      "workspace": str(ws), "is_default": False, "bindings": 0},
        }

    def delete_agent(self, agent_id: str) -> dict:
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first."}
        aid = (agent_id or "").strip()
        if not aid:
            return {"ok": False, "message": "No agent id given."}
        if aid == "main":
            return {"ok": False, "message": "The default agent can't be deleted."}
        code, out, err = process._run(["openclaw", "agents", "delete", aid, "--force", "--json"], timeout=60)
        ok = code == 0
        if ok:
            invalidate_agents_cache()
        logger.info("openclaw agents delete id=%s ok=%s", aid, ok)
        return {"ok": ok, "message": "Agent deleted." if ok else (err or out or "Couldn't delete.")[-400:]}

    def handoff_file(self, *, from_agent_id: str, to_agent_id: str, file_name: str) -> dict:
        """Copy a working file from one agent's workspace to another's, so the next
        agent can keep working on the same file (the file flows through the team).
        Confined to the agents' own workspaces; no path traversal."""
        import shutil

        name = (file_name or "").strip()
        if not re.match(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,118}$", name):
            return {"ok": False, "message": "Invalid file name."}
        src_ws = self._agent_workspace(from_agent_id)
        dst_ws = self._agent_workspace(to_agent_id)
        if src_ws is None or dst_ws is None or not src_ws.exists():
            return {"ok": False, "message": "Couldn't find the agent workspaces."}
        src = src_ws / name
        try:
            if src.resolve().parent != src_ws.resolve() or not src.is_file():
                return {"ok": False, "message": f"'{name}' isn't in {from_agent_id}'s folder yet."}
            dst_ws.mkdir(parents=True, exist_ok=True)
            dst = dst_ws / name
            shutil.copy2(src, dst)
        except OSError as exc:
            return {"ok": False, "message": f"Couldn't copy the file: {exc}"}
        logger.info("openclaw file handoff %s->%s file=%s", from_agent_id, to_agent_id, name)
        return {"ok": True, "message": f"Sent {name} to {to_agent_id}.", "path": str(dst)}

    def agent_chat(self, *, agent_id: str, message: str, session_id: str | None = None) -> dict:
        """Run one agent turn via OpenClaw and return the reply — so Evano can chat
        with an OpenClaw agent natively (no dashboard). A stable session_id keeps
        conversation continuity (the agent remembers earlier turns). Uses the
        gateway, falling back to the embedded agent automatically."""
        if process._which("openclaw") is None:
            return {"ok": False, "reply": "", "model": "", "session_id": "", "message": "Install OpenClaw first."}
        aid = (agent_id or "").strip()
        if not aid:
            return {"ok": False, "reply": "", "model": "", "session_id": "", "message": "No agent id."}
        if not message or not message.strip():
            return {"ok": False, "reply": "", "model": "", "session_id": "", "message": "Type a message first."}
        # Only accept a safe session id; anything else is ignored (new session).
        sid = (session_id or "").strip()
        if sid and not re.match(r"^[A-Za-z0-9_-]{1,80}$", sid):
            sid = ""
        args = ["openclaw", "agent", "--agent", aid, "--message", message.strip()]
        if sid:
            args += ["--session-id", sid]
        args += ["--json"]
        code, out, err = process._run(args, timeout=180)
        if not out:
            return {"ok": False, "reply": "", "model": "", "session_id": sid, "message": (err or "The agent didn't respond.")[-400:]}
        try:
            data = json.loads(out)
        except Exception:  # noqa: BLE001
            return {"ok": False, "reply": "", "model": "", "session_id": sid, "message": "Couldn't read the agent reply."}
        payloads = data.get("payloads") or []
        reply = "\n".join(p.get("text", "") for p in payloads if isinstance(p, dict) and p.get("text"))
        meta = data.get("meta") or {}
        if not reply:
            reply = meta.get("finalAssistantVisibleText") or ""
        model = ((meta.get("agentMeta") or {}).get("model")) or ""
        used_sid = ((meta.get("agentMeta") or {}).get("sessionId")) or sid
        ok = bool(reply)
        logger.info("openclaw agent chat agent=%s session=%s ok=%s", aid, used_sid, ok)
        return {"ok": ok, "reply": reply or "(no reply)", "model": model, "session_id": used_sid,
                "message": "" if ok else "The agent returned an empty reply."}

    def list_sessions(self, agent_id: str) -> dict:
        """List saved conversations for an agent, read straight from OpenClaw's own
        on-disk session store — so history survives closing/reopening Evano."""
        sdir = self._agent_sessions_dir(agent_id)
        if sdir is None:
            return {"ok": False, "message": "Invalid agent.", "sessions": [], "total_bytes": 0}
        if not sdir.exists():
            return {"ok": True, "message": "", "sessions": [], "total_bytes": 0}
        key_by_sid = self._session_keys(sdir)
        sessions = []
        for jf in sdir.glob("*.jsonl"):
            if jf.name.endswith(".trajectory.jsonl"):
                continue  # the big trace file, not the conversation
            sid = jf.name[: -len(".jsonl")]
            preview, count = self._session_preview(jf)
            if count == 0:
                continue  # empty/placeholder session
            try:
                updated = int(jf.stat().st_mtime * 1000)
            except OSError:
                updated = 0
            sessions.append({
                "session_id": sid,
                "preview": preview,
                "message_count": count,
                "updated_at": updated,
                "size_bytes": self._session_size(sdir, sid),
                "origin": self._session_origin(sid, key_by_sid.get(sid, "")),
            })
        sessions.sort(key=lambda s: s["updated_at"], reverse=True)
        return {"ok": True, "message": "", "sessions": sessions, "total_bytes": self._dir_size(sdir)}

    def get_session(self, agent_id: str, session_id: str) -> dict:
        sdir = self._agent_sessions_dir(agent_id)
        if sdir is None or not re.match(r"^[A-Za-z0-9_-]{1,80}$", session_id or ""):
            return {"ok": False, "message": "Invalid conversation.", "messages": []}
        jf = sdir / f"{session_id}.jsonl"
        if not jf.is_file():
            return {"ok": False, "message": "Conversation not found.", "messages": []}
        messages = []
        try:
            for line in jf.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    obj = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                if obj.get("type") != "message":
                    continue
                m = obj.get("message") or {}
                role = m.get("role")
                if role not in ("user", "assistant"):
                    continue
                text = "".join(
                    c.get("text", "") for c in (m.get("content") or [])
                    if isinstance(c, dict) and c.get("type") == "text"
                )
                if text:
                    messages.append({"role": role, "content": text})
        except OSError as exc:
            return {"ok": False, "message": f"Couldn't read conversation: {exc}", "messages": []}
        return {"ok": True, "message": "", "messages": messages}

    def delete_session(self, agent_id: str, session_id: str) -> dict:
        sdir = self._agent_sessions_dir(agent_id)
        if sdir is None or not re.match(r"^[A-Za-z0-9_-]{1,80}$", session_id or ""):
            return {"ok": False, "message": "Invalid conversation."}
        removed = self._remove_session_files(sdir, session_id)
        self._prune_sessions_index(sdir, {session_id})
        logger.info("openclaw session delete agent=%s session=%s removed=%s", agent_id, session_id, removed)
        return {"ok": removed > 0, "message": "Conversation deleted." if removed else "Nothing to delete."}

    def clear_sessions(self, agent_id: str, older_than_days: int | None = None) -> dict:
        """Delete all conversations for an agent (or only those older than N days).
        Gives clients control over how much chat history takes up disk."""
        sdir = self._agent_sessions_dir(agent_id)
        if sdir is None:
            return {"ok": False, "message": "Invalid agent.", "deleted": 0, "freed_bytes": 0}
        if not sdir.exists():
            return {"ok": True, "message": "Nothing to clear.", "deleted": 0, "freed_bytes": 0}
        cutoff = None
        if older_than_days and older_than_days > 0:
            cutoff = time.time() - older_than_days * 86400
        removed_ids, freed = set(), 0
        for jf in list(sdir.glob("*.jsonl")):
            if jf.name.endswith(".trajectory.jsonl"):
                continue
            sid = jf.name[: -len(".jsonl")]
            try:
                if cutoff is not None and jf.stat().st_mtime >= cutoff:
                    continue
            except OSError:
                continue
            freed += self._session_size(sdir, sid)
            self._remove_session_files(sdir, sid)
            removed_ids.add(sid)
        if removed_ids:
            self._prune_sessions_index(sdir, removed_ids)
        logger.info("openclaw sessions clear agent=%s deleted=%s", agent_id, len(removed_ids))
        return {"ok": True, "message": "", "deleted": len(removed_ids), "freed_bytes": freed}

    # ---- agent config files (read/edit what OpenClaw scaffolds) --------- #

    def get_agent_files(self, agent_id: str) -> dict:
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first.", "workspace": "", "files": []}
        ws = self._agent_workspace(agent_id)
        if ws is None or not ws.exists():
            return {"ok": False, "message": "Couldn't find this agent's workspace.", "workspace": "", "files": []}
        names = list(metadata._AGENT_FILE_ORDER)
        for p in sorted(ws.glob("*.md")):
            if p.name not in names:
                names.append(p.name)
        files = []
        for name in names:
            path = ws / name
            exists = path.is_file()
            content, size = "", 0
            if exists:
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")[:200_000]
                    size = path.stat().st_size
                except OSError:
                    exists = False
            if not exists and name not in metadata._AGENT_FILE_LABELS:
                continue  # skip unknown files that don't exist
            files.append({
                "name": name,
                "label": metadata._AGENT_FILE_LABELS.get(name, name),
                "size": size,
                "content": content,
                "exists": exists,
            })
        return {"ok": True, "message": "", "workspace": str(ws), "files": files}

    def save_agent_file(self, *, agent_id: str, name: str, content: str | None) -> dict:
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first."}
        if not metadata._AGENT_FILE_RE.match(name or ""):
            return {"ok": False, "message": "Only .md config files can be edited."}
        ws = self._agent_workspace(agent_id)
        if ws is None or not ws.exists():
            return {"ok": False, "message": "Couldn't find this agent's workspace."}
        target = ws / name
        try:  # defense in depth: the file must live directly in the workspace
            if target.resolve().parent != ws.resolve():
                return {"ok": False, "message": "Invalid file path."}
        except OSError:
            return {"ok": False, "message": "Invalid file path."}
        body = content or ""
        if len(body) > 500_000:
            return {"ok": False, "message": "That file is too large to save."}
        try:
            target.write_text(body, encoding="utf-8")
        except OSError as exc:
            return {"ok": False, "message": f"Couldn't save: {exc}"}
        logger.info("openclaw agent file saved agent=%s file=%s", agent_id, name)
        return {"ok": True, "message": "Saved."}

    def list_all_chats(self) -> dict:
        """Every conversation of every agent, grouped — powers the Chats tab."""
        agents_res = self.list_agents()
        if not agents_res.get("ok"):
            return {"ok": False, "message": agents_res.get("message") or "", "agents": []}
        identities = self._config_identities()
        groups = []
        for a in agents_res.get("agents") or []:
            ident = identities.get(a["id"], {})
            listing = self.list_sessions(a["id"])
            sessions = listing.get("sessions") or []
            groups.append({
                "agent_id": a["id"],
                "name": ident.get("name") or a.get("name") or a["id"],
                "emoji": ident.get("emoji") or "",
                "sessions": sessions,
            })
        # Agents with chats first, freshest activity on top.
        groups.sort(key=lambda g: max((s["updated_at"] for s in g["sessions"]), default=0), reverse=True)
        return {"ok": True, "message": "", "agents": groups}

    def _config_identities(self) -> dict[str, dict]:
        """Friendly name/emoji per agent id from openclaw.json (best-effort)."""
        try:
            cfg = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8")) if config.CONFIG_FILE.exists() else {}
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

    def _session_keys(self, sdir: Path) -> dict[str, str]:
        """sessionId → routing key, from OpenClaw's sessions.json index. The key
        encodes where the chat lives (e.g. "agent:main:discord:channel:…")."""
        idx = sdir / "sessions.json"
        if not idx.is_file():
            return {}
        try:
            data = json.loads(idx.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
        out: dict[str, str] = {}
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, dict) and val.get("sessionId"):
                    out[str(val["sessionId"])] = str(key)
        return out

    @staticmethod
    def _session_origin(session_id: str, key: str) -> str:
        """Classify where a conversation came from (session id + routing key)."""
        if session_id.startswith("evano-team-"):
            return "team"
        if session_id.startswith("evano-"):
            return "evano"
        key_l = key.lower()
        for channel in ("discord", "telegram", "whatsapp", "slack", "signal", "imessage"):
            if f":{channel}" in key_l or key_l.startswith(f"{channel}:"):
                return channel
        if ":subagent" in key_l:
            return "subagent"
        if ":cron" in key_l or key_l.startswith("cron"):
            return "cron"
        if key_l.endswith(":main") or key_l == "main":
            return "dashboard"
        return "other"

    def _agent_sessions_dir(self, agent_id: str) -> Path | None:
        """OpenClaw stores sessions at ~/.openclaw/agents/<id>/sessions."""
        aid = (agent_id or "").strip()
        if not re.match(r"^[A-Za-z0-9_-]{1,60}$", aid):
            return None
        return config.CONFIG_DIR / "agents" / aid / "sessions"

    def _session_preview(self, jsonl_file: Path) -> tuple[str, int]:
        """First user message (truncated) + message count, from a session .jsonl."""
        preview, count = "", 0
        try:
            for line in jsonl_file.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    obj = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                if obj.get("type") != "message":
                    continue
                m = obj.get("message") or {}
                if m.get("role") not in ("user", "assistant"):
                    continue
                count += 1
                if not preview and m.get("role") == "user":
                    text = "".join(
                        c.get("text", "") for c in (m.get("content") or [])
                        if isinstance(c, dict) and c.get("type") == "text"
                    )
                    preview = " ".join(text.split())[:80]
        except OSError:
            return "", 0
        return preview or "(no preview)", count

    def _session_size(self, sdir: Path, sid: str) -> int:
        total = 0
        for suffix in (".jsonl", ".trajectory.jsonl", ".trajectory-path.json"):
            p = sdir / f"{sid}{suffix}"
            try:
                if p.is_file():
                    total += p.stat().st_size
            except OSError:
                pass
        return total

    def _dir_size(self, d: Path) -> int:
        total = 0
        try:
            for p in d.rglob("*"):
                if p.is_file():
                    try:
                        total += p.stat().st_size
                    except OSError:
                        pass
        except OSError:
            pass
        return total

    def _remove_session_files(self, sdir: Path, sid: str) -> int:
        removed = 0
        for suffix in (".jsonl", ".trajectory.jsonl", ".trajectory-path.json"):
            p = sdir / f"{sid}{suffix}"
            try:
                if p.is_file() and p.resolve().parent == sdir.resolve():
                    p.unlink()
                    removed += 1
            except OSError:
                pass
        return removed

    def _prune_sessions_index(self, sdir: Path, sids: set[str]) -> None:
        """Remove deleted sessions from OpenClaw's sessions.json index so they
        don't linger as broken entries."""
        idx = sdir / "sessions.json"
        if not idx.is_file():
            return
        try:
            data = json.loads(idx.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return
        if not isinstance(data, dict):
            return
        kept = {k: v for k, v in data.items()
                if not (isinstance(v, dict) and v.get("sessionId") in sids)}
        if len(kept) != len(data):
            try:
                idx.write_text(json.dumps(kept), encoding="utf-8")
            except OSError:
                pass

    def _agent_workspace(self, agent_id: str) -> Path | None:
        """Resolve an agent's workspace dir (via the cached agent list)."""
        aid = (agent_id or "").strip()
        if not aid:
            return None
        for a in self.list_agents().get("agents") or []:
            if a.get("id") == aid and a.get("workspace"):
                return Path(a["workspace"])
        return None
