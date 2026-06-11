"""Shared pytest fixtures.

Each test gets an app backed by an isolated SQLite database in a temp directory,
so tests never touch the real local data directory.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _reset_openclaw_agents_cache() -> Iterator[None]:
    """The agents-list cache is process-global; never let it leak across tests."""
    from app.services.openclaw_service._agents import invalidate_agents_cache
    from app.services.openclaw_service._support import invalidate_bindings_cache

    invalidate_agents_cache()
    invalidate_bindings_cache()
    yield
    invalidate_agents_cache()
    invalidate_bindings_cache()


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(data_dir=tmp_path, environment="test")
    app = create_app(settings)
    # The context manager runs the lifespan (engine + table creation).
    with TestClient(app) as test_client:
        yield test_client
