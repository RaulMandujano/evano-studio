"""Shared model building blocks."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel

from ..utils.time import utc_now


class TimestampMixin(SQLModel):
    """Adds ``created_at`` / ``updated_at`` columns.

    ``updated_at`` is refreshed by the database on UPDATE via SQLAlchemy's
    ``onupdate`` hook.
    """

    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
