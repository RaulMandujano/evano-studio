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


@pytest.fixture()
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(data_dir=tmp_path, environment="test")
    app = create_app(settings)
    # The context manager runs the lifespan (engine + table creation).
    with TestClient(app) as test_client:
        yield test_client
