"""WhatsApp QR login, INSIDE Evano — no dashboard detour, no terminal.

`openclaw channels login --channel whatsapp` prints a live QR code to the
terminal (WhatsApp Web pairing). We run that exact command in the background,
parse the block-character QR art from its output into a module matrix, and
re-render it as a crisp SVG the desktop app shows inline. The user scans it
with their phone like WhatsApp Web; the CLI process completes the link.

The SVG reproduces the terminal image faithfully (light modules on dark),
which is exactly what people scan from terminals every day.
"""

from __future__ import annotations

import logging
import re
import subprocess
import threading
import time
from collections import deque

from . import process

logger = logging.getLogger("evano.agent_engine.openclaw")

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_BLOCK_CHARS = {"█", "▀", "▄"}
_LOGIN_TIMEOUT_SECONDS = 240.0
_SUCCESS_HINTS = ("logged in", "login successful", "linked", "connected", "paired", "authenticated")


def _is_qr_line(line: str) -> bool:
    stripped = line.rstrip()
    if len(stripped) < 16:
        return False
    blocks = sum(1 for ch in stripped if ch in _BLOCK_CHARS)
    others = sum(1 for ch in stripped if ch not in _BLOCK_CHARS and ch != " ")
    return blocks >= 4 and others == 0


def parse_qr_block(lines: list[str]) -> list[list[bool]] | None:
    """Turn terminal QR art into a module matrix (True = light/block cell).

    Handles the two common styles:
    - half-block: each char is two vertical modules (▀ top, ▄ bottom, █ both)
    - full-block: each module is two chars wide (██ or two spaces), one per line
    """
    if len(lines) < 8:
        return None
    width = max(len(l.rstrip()) for l in lines)
    half_block = any(("▀" in l or "▄" in l) for l in lines)
    matrix: list[list[bool]] = []
    if half_block:
        for line in lines:
            padded = line.rstrip().ljust(width)
            top: list[bool] = []
            bottom: list[bool] = []
            for ch in padded:
                top.append(ch in ("█", "▀"))
                bottom.append(ch in ("█", "▄"))
            matrix.append(top)
            matrix.append(bottom)
    else:
        for line in lines:
            padded = line.rstrip().ljust(width)
            # double-width modules: sample every second column
            matrix.append([padded[i] == "█" for i in range(0, width, 2)])
    # Sanity: a QR is roughly square and at least 21 modules.
    rows = len(matrix)
    cols = max(len(r) for r in matrix)
    if rows < 21 or cols < 21:
        return None
    return matrix


def matrix_to_svg(matrix: list[list[bool]], scale: int = 6, quiet: int = 4) -> str:
    """Render the matrix as the terminal shows it: light modules on dark."""
    rows = len(matrix)
    cols = max(len(r) for r in matrix)
    w = (cols + quiet * 2) * scale
    h = (rows + quiet * 2) * scale
    rects = []
    for y, row in enumerate(matrix):
        for x, lit in enumerate(row):
            if lit:
                rects.append(
                    f'<rect x="{(x + quiet) * scale}" y="{(y + quiet) * scale}" '
                    f'width="{scale}" height="{scale}"/>'
                )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="#000"/>'
        f'<g fill="#fff">{"".join(rects)}</g></svg>'
    )


class WhatsAppLoginManager:
    """One login attempt at a time; the desktop polls status() while it runs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: subprocess.Popen | None = None
        self._state = "idle"  # idle | starting | qr | connected | error | expired
        self._matrix: list[list[bool]] | None = None
        self._tail: deque[str] = deque(maxlen=30)
        self._started_at = 0.0

    def start(self, account: str | None = None) -> dict:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                return self._status_locked()
            exe = process._which("openclaw")
            if exe is None:
                return {"state": "error", "qr_svg": None, "message": "Install OpenClaw first."}
            # First-time logins hit an interactive "Install WhatsApp plugin?"
            # picker that a background process can't answer — install it
            # non-interactively up front (no-op when already installed).
            self._ensure_plugin()
            args = [exe, "channels", "login", "--channel", "whatsapp"]
            if account:
                args += ["--account", account]
            try:
                self._proc = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
            except OSError as exc:
                return {"state": "error", "qr_svg": None, "message": f"Couldn't start the login: {exc}"}
            self._state = "starting"
            self._matrix = None
            self._tail.clear()
            self._started_at = time.monotonic()
            threading.Thread(target=self._pump, args=(self._proc,), daemon=True).start()
            threading.Thread(target=self._watchdog, args=(self._proc,), daemon=True).start()
            logger.info("whatsapp login started")
            return self._status_locked()

    def status(self) -> dict:
        with self._lock:
            return self._status_locked()

    def cancel(self) -> dict:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                try:
                    self._proc.kill()
                except OSError:
                    pass
            self._proc = None
            self._state = "idle"
            self._matrix = None
            logger.info("whatsapp login canceled")
            return self._status_locked()

    # ---- internals -------------------------------------------------------- #

    @staticmethod
    def _ensure_plugin() -> None:
        """Install the WhatsApp channel plugin if it's missing (best-effort)."""
        code, out, _ = process._run(["openclaw", "plugins", "list"], timeout=30)
        if code == 0 and "whatsapp" in out.lower():
            return
        code, out, err = process._run(
            ["openclaw", "plugins", "install", "clawhub:@openclaw/whatsapp"], timeout=180
        )
        logger.info("whatsapp plugin install ok=%s", code == 0)

    def _status_locked(self) -> dict:
        svg = matrix_to_svg(self._matrix) if self._matrix and self._state == "qr" else None
        return {
            "state": self._state,
            "qr_svg": svg,
            "message": " · ".join(list(self._tail)[-3:]),
        }

    def _pump(self, proc: subprocess.Popen) -> None:
        qr_lines: list[str] = []
        assert proc.stdout is not None
        for raw in proc.stdout:
            line = _ANSI_RE.sub("", raw.rstrip("\n"))
            if _is_qr_line(line):
                qr_lines.append(line)
                continue
            # A QR block just ended — parse and publish it (QRs refresh, keep latest).
            if qr_lines:
                matrix = parse_qr_block(qr_lines)
                qr_lines = []
                if matrix:
                    with self._lock:
                        if self._proc is proc:
                            self._matrix = matrix
                            self._state = "qr"
            text = line.strip()
            if text:
                with self._lock:
                    if self._proc is proc:
                        self._tail.append(text[:160])
                if any(hint in text.lower() for hint in _SUCCESS_HINTS):
                    with self._lock:
                        if self._proc is proc:
                            self._state = "connected"
        code = proc.wait()
        with self._lock:
            if self._proc is not proc:
                return  # canceled / replaced
            if self._state == "connected" or code == 0:
                self._state = "connected"
            elif self._state != "expired":
                self._state = "error"
            self._matrix = None
            self._proc = None
        if self._state == "connected":
            logger.info("whatsapp login connected")

    def _watchdog(self, proc: subprocess.Popen) -> None:
        while proc.poll() is None:
            if time.monotonic() - self._started_at > _LOGIN_TIMEOUT_SECONDS:
                with self._lock:
                    if self._proc is proc:
                        self._state = "expired"
                        self._matrix = None
                try:
                    proc.kill()
                except OSError:
                    pass
                logger.info("whatsapp login expired (timeout)")
                return
            time.sleep(2)


_whatsapp_login = WhatsAppLoginManager()


class WhatsAppLoginMixin:
    def whatsapp_login_start(self, account: str | None = None) -> dict:
        return _whatsapp_login.start(account)

    def whatsapp_login_status(self) -> dict:
        return _whatsapp_login.status()

    def whatsapp_login_cancel(self) -> dict:
        return _whatsapp_login.cancel()
