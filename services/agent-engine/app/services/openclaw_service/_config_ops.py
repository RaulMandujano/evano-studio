"""Config + web-search mixin: write OpenClaw config, read its summary."""
from __future__ import annotations

import json
import logging
import time

from . import config, process

logger = logging.getLogger("evano.agent_engine.openclaw")


class ConfigMixin:
    def write_config(
        self, *, mode: str, model: str, api_key: str | None, provider: str | None, base_url: str | None
    ) -> dict:
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first.", "config": self._read_config_summary()}

        if mode == "free":
            args = [
                "openclaw", "onboard", "--non-interactive", "--auth-choice", "ollama",
                "--custom-base-url", base_url or config.DEFAULT_OLLAMA_URL,
                "--custom-model-id", model or "gemma4:latest", "--accept-risk",
            ]
            code, out, err = process._run(args, timeout=180)
        else:
            prov = (provider or "anthropic").strip()
            extra = {f"{prov.upper()}_API_KEY": api_key} if api_key else {}
            args = ["openclaw", "onboard", "--non-interactive", "--auth-choice", prov, "--accept-risk"]
            code, out, err = process._run(args, timeout=180, env=process._env(extra))

        ok = code == 0 and config.CONFIG_FILE.exists()
        if ok:
            self._ensure_web_search()  # free DuckDuckGo web search by default
        msg = "Configured." if ok else (err or out or "Configuration failed.")[-400:]
        logger.info("openclaw onboard mode=%s ok=%s", mode, ok)
        return {"ok": ok, "message": msg, "config": self._read_config_summary()}

    # ---- web search (free, no API key) --------------------------------- #

    def enable_web_search(self, provider: str = "duckduckgo") -> dict:
        """Set the default web-search provider so agents can search the internet.
        DuckDuckGo needs no API key (free)."""
        if process._which("openclaw") is None:
            return {"ok": False, "message": "Install OpenClaw first.", "web_search": self._web_search_info()}
        code, out, err = process._run(["openclaw", "config", "set", "tools.web.search.provider", provider], timeout=30)
        ok = code == 0
        logger.info("openclaw web search provider=%s ok=%s", provider, ok)
        # The gateway caches config; restart it if running so the change applies now.
        if ok and process._port_open(self._gateway_port()):
            process._run(["openclaw", "gateway", "stop"], timeout=30)
            process._run(["openclaw", "gateway", "start"], timeout=60)
            for _ in range(10):
                if process._port_open(self._gateway_port()):
                    break
                time.sleep(0.5)
        return {
            "ok": ok,
            "message": "Free web search enabled (DuckDuckGo)." if ok else (err or out or "Couldn't enable web search.")[-300:],
            "web_search": self._web_search_info(),
        }

    def _ensure_web_search(self) -> None:
        """Enable free DuckDuckGo search if no provider is configured (don't clobber
        a user's paid provider)."""
        if not self._web_search_provider():
            process._run(["openclaw", "config", "set", "tools.web.search.provider", "duckduckgo"], timeout=30)

    def _gateway_token(self) -> str | None:
        try:
            data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8")) if config.CONFIG_FILE.exists() else {}
            token = (((data.get("gateway") or {}).get("auth") or {}).get("token"))
            return token if isinstance(token, str) and token else None
        except Exception:  # noqa: BLE001
            return None

    def _web_search_provider(self) -> str | None:
        try:
            data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8")) if config.CONFIG_FILE.exists() else {}
            prov = ((((data.get("tools") or {}).get("web") or {}).get("search") or {}).get("provider"))
            return prov if isinstance(prov, str) and prov else None
        except Exception:  # noqa: BLE001
            return None

    def _web_search_info(self) -> dict:
        prov = self._web_search_provider()
        return {"provider": prov, "enabled": prov is not None}

    def _gateway_port(self, cfg: dict | None = None) -> int:
        try:
            data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8")) if config.CONFIG_FILE.exists() else {}
            return int(data.get("gateway", {}).get("port", config.DEFAULT_GATEWAY_PORT))
        except Exception:  # noqa: BLE001
            return config.DEFAULT_GATEWAY_PORT

    def _read_config_summary(self) -> dict:
        if not config.CONFIG_FILE.exists():
            return {"exists": False, "path": str(config.CONFIG_FILE), "provider": None, "model": None}
        provider = model = None
        try:
            data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8"))
            primary = (((data.get("agents") or {}).get("defaults") or {}).get("model") or {}).get("primary")
            if isinstance(primary, str) and "/" in primary:
                provider, model = primary.split("/", 1)
            elif isinstance(primary, str):
                model = primary
        except Exception:  # noqa: BLE001
            pass
        return {"exists": True, "path": str(config.CONFIG_FILE), "provider": provider, "model": model}
