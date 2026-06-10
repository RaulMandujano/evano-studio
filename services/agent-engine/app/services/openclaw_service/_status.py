"""Status mixin: prerequisite detection + overall readiness."""
from __future__ import annotations

from . import process


class StatusMixin:
    def status(self) -> dict:
        node = process._version("node")
        openclaw_installed = process._which("openclaw") is not None
        cfg = self._read_config_summary()
        port = self._gateway_port(cfg)
        gateway_running = process._port_open(port)
        return {
            "node": {"installed": node is not None, "version": node},
            "npm": {"installed": process._version("npm") is not None, "version": process._version("npm")},
            "ollama": {"installed": process._version("ollama") is not None, "version": process._version("ollama")},
            "openclaw": {
                "installed": openclaw_installed,
                "version": process._version("openclaw") if openclaw_installed else None,
            },
            "config": cfg,
            "gateway": {"running": gateway_running, "port": port},
            "web_search": self._web_search_info(),
            "ready": bool(node and openclaw_installed and cfg["exists"]),
        }
