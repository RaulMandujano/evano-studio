"""OpenClaw config file location and defaults.

CONFIG_DIR/CONFIG_FILE are module attributes (not `from … import`) so tests can
redirect them to a temp dir via monkeypatch and every reader sees the change.
"""
from __future__ import annotations

from pathlib import Path

CONFIG_DIR = Path.home() / ".openclaw"
CONFIG_FILE = CONFIG_DIR / "openclaw.json"  # OpenClaw's real config (JSON)
DEFAULT_GATEWAY_PORT = 18789
DEFAULT_OLLAMA_URL = "http://localhost:11434"
