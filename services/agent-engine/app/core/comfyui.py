"""Effective ComfyUI configuration (DB overrides + env defaults).

ComfyUI settings are user-editable at runtime (desktop Settings), so they live
in the app_settings table, falling back to the env-driven defaults.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session

from .config import Settings

_BASE_URL = "comfyui_base_url"
_ENABLED = "comfyui_enabled"
_WORKFLOW = "comfyui_default_workflow_path"
_TRUTHY = {"1", "true", "yes", "on"}


@dataclass
class ComfyUIConfig:
    base_url: str
    enabled: bool
    default_workflow_path: str


def _get(session: Session, key: str) -> str | None:
    from ..db.models import AppSetting

    row = session.get(AppSetting, key)
    if row is not None and row.value.strip():
        return row.value.strip()
    return None


def get_comfyui_config(session: Session, settings: Settings) -> ComfyUIConfig:
    base_url = _get(session, _BASE_URL) or settings.comfyui_base_url
    enabled_raw = _get(session, _ENABLED)
    enabled = enabled_raw.lower() in _TRUTHY if enabled_raw is not None else settings.comfyui_enabled
    workflow = _get(session, _WORKFLOW) or settings.comfyui_default_workflow_path
    return ComfyUIConfig(base_url=base_url.rstrip("/"), enabled=enabled, default_workflow_path=workflow)


def set_comfyui_config(
    session: Session,
    *,
    base_url: str | None = None,
    enabled: bool | None = None,
    default_workflow_path: str | None = None,
) -> None:
    from ..db.models import AppSetting

    updates: dict[str, str] = {}
    if base_url is not None:
        updates[_BASE_URL] = base_url.strip()
    if enabled is not None:
        updates[_ENABLED] = "true" if enabled else "false"
    if default_workflow_path is not None:
        updates[_WORKFLOW] = default_workflow_path.strip()

    for key, value in updates.items():
        row = session.get(AppSetting, key)
        if row is None:
            session.add(AppSetting(key=key, value=value))
        else:
            row.value = value
            session.add(row)
    session.commit()
