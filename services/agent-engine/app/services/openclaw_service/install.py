"""Background OpenClaw install (`npm install -g openclaw`)."""
from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass

from . import process

@dataclass
class _InstallState:
    state: str = "idle"  # idle | running | success | error
    message: str = ""
    log_tail: str = ""


class _InstallManager:
    """Runs `npm install -g openclaw` in a background thread."""

    def __init__(self) -> None:
        self._state = _InstallState()
        self._lock = threading.Lock()

    def status(self) -> _InstallState:
        with self._lock:
            return _InstallState(self._state.state, self._state.message, self._state.log_tail)

    def start(self) -> _InstallState:
        with self._lock:
            if self._state.state == "running":
                return self.status()
            self._state = _InstallState(state="running", message="Installing OpenClaw…")
        threading.Thread(target=self._run, name="evano-openclaw-install", daemon=True).start()
        return self.status()

    def _set(self, **kw) -> None:
        with self._lock:
            for k, v in kw.items():
                setattr(self._state, k, v)

    def _run(self) -> None:
        npm = process._which("npm")
        if npm is None:
            self._set(state="error", message="npm (Node.js) is not installed.")
            return
        try:
            proc = subprocess.run(
                [npm, "install", "-g", "openclaw"],
                capture_output=True, text=True, timeout=600, env=process._env(),
            )
            tail = ((proc.stdout or "") + (proc.stderr or ""))[-1500:]
            if proc.returncode == 0 and process._which("openclaw"):
                self._set(state="success", message="OpenClaw installed.", log_tail=tail)
            else:
                self._set(state="error", message="Install failed. See details.", log_tail=tail)
        except subprocess.TimeoutExpired:
            self._set(state="error", message="Install timed out (network?).")
        except Exception as exc:  # noqa: BLE001
            self._set(state="error", message=str(exc))


_install_manager = _InstallManager()
