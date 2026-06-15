"""One-click download + launch of the OFFICIAL Node.js / Ollama installers.

Evano never silently installs system software or uses sudo. Instead it does the
tedious part for the user: it figures out the right official installer for their
OS/arch, downloads it into a temp folder, and launches it — so the normal
installer wizard appears with a single click instead of "open browser → find the
right file → download → run". The user still approves the OS-level install.

Mirrors the background-thread pattern used by ``install.py`` (OpenClaw via npm).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

import httpx

# Stable "latest" URLs published by the projects themselves.
_OLLAMA_WIN = "https://github.com/ollama/ollama/releases/latest/download/OllamaSetup.exe"
_OLLAMA_MAC = "https://github.com/ollama/ollama/releases/latest/download/Ollama.dmg"
_NODE_INDEX = "https://nodejs.org/dist/index.json"


@dataclass
class _PrereqState:
    # idle | downloading | launching | launched | error
    state: str = "idle"
    message: str = ""
    percent: int = 0
    download_url: str = ""  # official page/file, surfaced as a manual fallback


def _downloads_dir() -> Path:
    d = Path(tempfile.gettempdir()) / "evano-installers"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resolve_node() -> tuple[str, str]:
    """(url, filename) for the official Node.js LTS installer on this platform.

    The LTS version is resolved live from nodejs.org so it never goes stale. The
    macOS ``.pkg`` is a universal installer (one file for Intel + Apple Silicon).
    """
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        data = client.get(_NODE_INDEX).json()
    lts = next((x for x in data if x.get("lts")), None)
    if not lts or not lts.get("version"):
        raise RuntimeError("Couldn't find a Node.js LTS release.")
    version = lts["version"]  # e.g. "v24.16.0"
    base = f"https://nodejs.org/dist/{version}"
    if sys.platform == "darwin":
        filename = f"node-{version}.pkg"
    elif sys.platform.startswith("win"):
        # Official Windows MSI is x64-only; it runs on Windows-on-ARM via emulation.
        filename = f"node-{version}-x64.msi"
    else:
        raise RuntimeError("Automatic Node.js install supports Windows and macOS.")
    return f"{base}/{filename}", filename


def _resolve_ollama() -> tuple[str, str]:
    if sys.platform == "darwin":
        return _OLLAMA_MAC, "Ollama.dmg"
    if sys.platform.startswith("win"):
        return _OLLAMA_WIN, "OllamaSetup.exe"
    raise RuntimeError("Automatic Ollama install supports Windows and macOS.")


def _manual_page(target: str) -> str:
    return "https://ollama.com/download" if target == "ollama" else "https://nodejs.org/en/download"


def _launch(path: Path) -> None:
    """Open the downloaded installer with the OS default handler."""
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]  # noqa: S606  (Windows-only)
    elif sys.platform == "darwin":
        subprocess.Popen(["/usr/bin/open", str(path)])
    else:
        raise RuntimeError("Unsupported platform.")


class _PrereqInstaller:
    """Downloads one official installer in a background thread, then launches it."""

    def __init__(self, target: str, resolver, friendly: str) -> None:
        self._target = target
        self._resolver = resolver
        self._friendly = friendly
        self._state = _PrereqState(download_url=_manual_page(target))
        self._lock = threading.Lock()

    def status(self) -> _PrereqState:
        with self._lock:
            s = self._state
            return _PrereqState(s.state, s.message, s.percent, s.download_url)

    def start(self) -> _PrereqState:
        with self._lock:
            if self._state.state in ("downloading", "launching"):
                return self.status()
            self._state = _PrereqState(
                state="downloading",
                message=f"Downloading {self._friendly}…",
                percent=0,
                download_url=_manual_page(self._target),
            )
        threading.Thread(
            target=self._run, name=f"evano-install-{self._target}", daemon=True
        ).start()
        return self.status()

    def _set(self, **kw) -> None:
        with self._lock:
            for k, v in kw.items():
                setattr(self._state, k, v)

    def _run(self) -> None:
        try:
            url, filename = self._resolver()
        except Exception as exc:  # noqa: BLE001
            self._set(state="error", message=f"Couldn't find the installer: {exc}")
            return
        dest = _downloads_dir() / filename
        try:
            with httpx.Client(timeout=None, follow_redirects=True) as client:
                with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("Content-Length") or 0)
                    written = 0
                    with open(dest, "wb") as fh:
                        for chunk in resp.iter_bytes(chunk_size=262_144):
                            fh.write(chunk)
                            written += len(chunk)
                            if total:
                                self._set(percent=min(99, int(written * 100 / total)))
        except Exception as exc:  # noqa: BLE001
            self._set(state="error", message=f"Download failed: {exc}")
            return
        self._set(state="launching", message="Opening the installer…", percent=100)
        try:
            _launch(dest)
        except Exception as exc:  # noqa: BLE001
            self._set(state="error", message=f"Couldn't open the installer: {exc}")
            return
        self._set(
            state="launched",
            message=(
                f"The {self._friendly} installer opened. Complete the steps in the "
                "installer window, then click Refresh."
            ),
        )


_managers: dict[str, _PrereqInstaller] = {
    "node": _PrereqInstaller("node", _resolve_node, "Node.js"),
    "ollama": _PrereqInstaller("ollama", _resolve_ollama, "Ollama"),
}


def _as_dict(s: _PrereqState) -> dict:
    return {
        "state": s.state,
        "message": s.message,
        "percent": s.percent,
        "download_url": s.download_url,
    }


def start(target: str) -> dict:
    mgr = _managers.get(target)
    if mgr is None:
        return {"state": "error", "message": f"Unknown installer: {target}", "percent": 0, "download_url": ""}
    return _as_dict(mgr.start())


def status(target: str) -> dict:
    mgr = _managers.get(target)
    if mgr is None:
        return {"state": "error", "message": f"Unknown installer: {target}", "percent": 0, "download_url": ""}
    return _as_dict(mgr.status())
