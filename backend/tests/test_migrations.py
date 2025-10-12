"""Tests covering database migrations."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.app.migrations import apply_migrations


def test_initial_migration(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    with Session() as session:
        apply_migrations(session)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "queue_jobs" in tables
    assert "encoding_profiles" in tables
