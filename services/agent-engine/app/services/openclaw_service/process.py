"""Low-level process primitives for the OpenClaw launcher.

Runs a FIXED set of OpenClaw/npm commands (never a shell) with a PATH augmented
for GUI-launched apps. Isolated here so tests can stub _run/_which.
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
from pathlib import Path

_EXTRA_PATHS = [
    str(Path.home() / ".npm-global" / "bin"),
    "/usr/local/bin",
    "/opt/homebrew/bin",
    "/opt/homebrew/sbin",
    "/usr/bin",
    "/bin",
]


def _env(extra: dict | None = None) -> dict:
    env = dict(os.environ)
    parts = env.get("PATH", "").split(os.pathsep)
    for p in _EXTRA_PATHS:
        if p and p not in parts:
            parts.append(p)
    env["PATH"] = os.pathsep.join(parts)
    if extra:
        env.update(extra)
    return env


def _which(cmd: str) -> str | None:
    return shutil.which(cmd, path=_env()["PATH"])


def _run(args: list[str], timeout: float = 15.0, env: dict | None = None) -> tuple[int, str, str]:
    exe = _which(args[0])
    if exe is None:
        return 127, "", f"{args[0]} not found"
    try:
        proc = subprocess.run(
            [exe, *args[1:]], capture_output=True, text=True, timeout=timeout, env=env or _env()
        )
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    except Exception as exc:  # noqa: BLE001
        return 1, "", str(exc)


def _version(cmd: str) -> str | None:
    if _which(cmd) is None:
        return None
    code, out, _ = _run([cmd, "--version"])
    return out.splitlines()[0].strip() if code == 0 and out else None


def _slugify(name: str) -> str:
    """A safe OpenClaw agent id from a friendly name (lowercase, dashed)."""
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return s[:40]


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False
