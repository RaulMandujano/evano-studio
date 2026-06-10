"""Install mixin: kick off / poll the background OpenClaw install."""
from __future__ import annotations

from . import install


class InstallMixin:
    def start_install(self) -> dict:
        s = install._install_manager.start()
        return {"state": s.state, "message": s.message, "log_tail": s.log_tail}

    def install_status(self) -> dict:
        s = install._install_manager.status()
        return {"state": s.state, "message": s.message, "log_tail": s.log_tail}
