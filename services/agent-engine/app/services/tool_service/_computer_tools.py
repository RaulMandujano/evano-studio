"""Computer-control + image-prompt tools (approval-gated for agents)."""
from __future__ import annotations

from ...db.models import Agent


class ComputerToolsMixin:
    def _tool_open_application(self, params: dict, agent: Agent | None) -> dict:
        from ..computer_service import ComputerService

        return ComputerService().open_application(str(params["app_name"]))

    def _tool_open_url(self, params: dict, agent: Agent | None) -> dict:
        from ..computer_service import ComputerService

        return ComputerService().open_url(str(params["url"]))

    def _tool_run_command(self, params: dict, agent: Agent | None) -> dict:
        from ..computer_service import ComputerService

        return ComputerService().run_command(str(params["command"]))

    def _tool_generate_image_prompt(self, params: dict, agent: Agent | None) -> dict:
        subject = str(params["subject"]).strip()
        style = str(params.get("style", "")).strip()
        details = str(params.get("details", "")).strip()
        parts = [subject]
        if style:
            parts.append(f"in a {style} style")
        if details:
            parts.append(details)
        parts.append("high detail, well composed, balanced lighting")
        prompt = ", ".join(parts)
        return {"prompt": prompt}

