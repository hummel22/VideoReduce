"""Migration runner for SQLite-based schema updates."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

MIGRATIONS_PATH = Path(__file__).resolve().parent.parent / "migrations"


def list_migration_files() -> Iterable[Path]:
    """Yield migration files ordered lexicographically by filename."""

    return sorted(MIGRATIONS_PATH.glob("*.sql"))


def apply_migrations(session: Session) -> None:
    """Apply pending migrations in order."""

    session.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_migrations (id INTEGER PRIMARY KEY AUTOINCREMENT, version TEXT NOT NULL UNIQUE, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    ))
    applied_versions = {
        row[0]
        for row in session.execute(text("SELECT version FROM schema_migrations"))
    }
    for migration_file in list_migration_files():
        version = migration_file.stem
        if version in applied_versions:
            continue
        with migration_file.open("r", encoding="utf-8") as handle:
            raw_connection = session.connection().connection
            raw_connection.executescript(handle.read())
        session.execute(
            text(
                "INSERT INTO schema_migrations (version) VALUES (:version) "
                "ON CONFLICT(version) DO NOTHING"
            ),
            {"version": version},
        )


def run_migrations() -> None:
    """Utility entry point to run migrations using a fresh session."""

    from .database import session_scope

    with session_scope() as session:
        apply_migrations(session)
