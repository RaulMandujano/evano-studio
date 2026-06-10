"""Settings service — read/write application settings (no HTTP here)."""

from __future__ import annotations

from sqlmodel import Session, select

from ..db.models import AppSetting
from ..utils.time import utc_now


class SettingsService:
    """CRUD for key/value application settings."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> dict[str, str]:
        rows = self._session.exec(select(AppSetting)).all()
        return {row.key: row.value for row in rows}

    def upsert_many(self, values: dict[str, str]) -> dict[str, str]:
        """Create or update each provided setting, then return all settings."""
        for key, value in values.items():
            existing = self._session.get(AppSetting, key)
            if existing is not None:
                existing.value = value
                existing.updated_at = utc_now()
                self._session.add(existing)
            else:
                self._session.add(AppSetting(key=key, value=value))
        self._session.commit()
        return self.get_all()
