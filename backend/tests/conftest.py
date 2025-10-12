"""Test fixtures shared across backend test modules."""
from __future__ import annotations

import importlib
import sys

import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings


@pytest.fixture()
def api_client(tmp_path, monkeypatch):
    """Provide a TestClient backed by an isolated SQLite database."""

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("VIDEOR_DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()

    modules_to_reload = [
        "backend.app.database",
        "backend.app.migrations",
        "backend.app.bootstrap",
        "backend.app.api.deps",
        "backend.app.api.analytics",
        "backend.app.api.users",
        "backend.app.main",
    ]
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)

    from backend.app.main import app

    with TestClient(app) as client:
        yield client
