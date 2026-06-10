"""Computer-control executor.

Runs real OS actions: open an app, open a URL, run a shell command. These are
powerful and intentionally NOT confined to the workspace. Safety is enforced at
two layers:

- When an AGENT requests one of these, it must be approved by a human first (the
  approval flow); this module only runs *after* approval, or from a manual
  Tools-page run (which is itself human-initiated).
- ``sudo`` (privilege escalation) is blocked outright, and commands have a
  timeout. Output is captured and bounded.

Every run is still recorded by ToolService's execution log.
"""

from __future__ import annotations

import logging
import platform
import subprocess
import webbrowser

from ..core.errors import AppError

logger = logging.getLogger("evano.agent_engine.tools")

_COMMAND_TIMEOUT = 60  # seconds
_MAX_STDOUT = 4000
_MAX_STDERR = 2000


def _is_sudo(command: str) -> bool:
    c = command.strip().lower()
    return c == "sudo" or c.startswith("sudo ") or " sudo " in f" {c} "


class ComputerService:
    """Executes approved computer-control actions on the local machine."""

    def open_application(self, app_name: str) -> dict:
        name = (app_name or "").strip()
        if not name:
            raise AppError("An application name is required.", status_code=400, code="invalid_params")
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["open", "-a", name], check=True, capture_output=True, text=True, timeout=20)
            elif system == "Windows":
                subprocess.run(["cmd", "/c", "start", "", name], check=True, capture_output=True, text=True, timeout=20)  # noqa: S607
            else:
                subprocess.Popen([name])  # best effort on Linux
        except subprocess.CalledProcessError as exc:
            raise AppError(
                f"Couldn't open '{name}': {(exc.stderr or '').strip() or exc}",
                status_code=400,
                code="open_failed",
            ) from exc
        except FileNotFoundError as exc:
            raise AppError(f"App '{name}' was not found.", status_code=404, code="not_found") from exc
        except Exception as exc:  # noqa: BLE001
            raise AppError(f"Couldn't open '{name}': {exc}", status_code=400, code="open_failed") from exc
        logger.info("computer: opened application %s", name)
        return {"success": True, "tool_name": "open_application", "app": name,
                "message": f"Opened {name}."}

    def open_url(self, url: str) -> dict:
        u = (url or "").strip()
        if not (u.startswith("http://") or u.startswith("https://")):
            raise AppError("Only http/https URLs can be opened.", status_code=400, code="invalid_url")
        webbrowser.open(u)
        logger.info("computer: opened url %s", u)
        return {"success": True, "tool_name": "open_url", "url": u, "message": f"Opened {u}."}

    def run_command(self, command: str) -> dict:
        cmd = (command or "").strip()
        if not cmd:
            raise AppError("A command is required.", status_code=400, code="invalid_params")
        if _is_sudo(cmd):
            raise AppError(
                "For safety, 'sudo' commands are blocked. Run admin tasks yourself.",
                status_code=400,
                code="blocked_command",
            )
        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=_COMMAND_TIMEOUT
            )
        except subprocess.TimeoutExpired as exc:
            raise AppError(
                f"Command timed out after {_COMMAND_TIMEOUT}s.", status_code=400, code="timeout"
            ) from exc
        logger.info("computer: ran command (exit=%s): %s", proc.returncode, cmd)
        return {
            "success": proc.returncode == 0,
            "tool_name": "run_command",
            "command": cmd,
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-_MAX_STDOUT:],
            "stderr": (proc.stderr or "")[-_MAX_STDERR:],
            "message": f"Command exited with code {proc.returncode}.",
        }
