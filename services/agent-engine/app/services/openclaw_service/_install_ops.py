"""Install mixin: kick off / poll the background OpenClaw + prerequisite installs."""
from __future__ import annotations

from . import install, prereq_install


class InstallMixin:
    def start_install(self) -> dict:
        s = install._install_manager.start()
        return {"state": s.state, "message": s.message, "log_tail": s.log_tail}

    def install_status(self) -> dict:
        s = install._install_manager.status()
        return {"state": s.state, "message": s.message, "log_tail": s.log_tail}

    # ---- Prerequisites (Node.js / Ollama): download + launch official installer
    def start_prereq_install(self, target: str) -> dict:
        return prereq_install.start(target)

    def prereq_install_status(self, target: str) -> dict:
        return prereq_install.status(target)
