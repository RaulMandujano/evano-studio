"""Gateway mixin: start/stop the gateway and build the dashboard URL."""
from __future__ import annotations

import time

from . import process


class GatewayMixin:
    def gateway_start(self) -> dict:
        code, out, err = process._run(["openclaw", "gateway", "start"], timeout=60)
        ok = code == 0
        port = self._gateway_port()
        # Give the service a moment to bind so we report accurate status.
        running = False
        for _ in range(10):
            if process._port_open(port):
                running = True
                break
            time.sleep(0.5)
        return {"ok": ok, "message": (out or err or "")[-400:], "running": running}

    def gateway_stop(self) -> dict:
        code, out, err = process._run(["openclaw", "gateway", "stop"], timeout=60)
        return {"ok": code == 0, "message": (out or err or "")[-400:], "running": process._port_open(self._gateway_port())}

    def dashboard_url(self) -> dict:
        # `--yes` starts/installs the gateway if needed so the URL is live.
        code, out, err = process._run(["openclaw", "dashboard", "--no-open", "--yes"], timeout=60)
        port = self._gateway_port()
        token = self._gateway_token()
        # Preferred: build the token-authenticated URL ourselves from the config
        # so the embedded dashboard logs in automatically (no copy/paste).
        if token:
            return {"ok": True, "url": f"http://127.0.0.1:{port}/#token={token}", "message": ""}
        # Fallback: parse a plain URL from the CLI output.
        url = None
        for line in (out + "\n" + err).splitlines():
            idx = line.find("http")
            if idx != -1:
                url = line[idx:].strip()
                break
        return {"ok": bool(url), "url": url, "message": (err or out or "")[-300:]}
