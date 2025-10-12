"""FastAPI application entry point."""
from __future__ import annotations

from . import compat as _compat  # noqa: F401  # Ensure compatibility patches run before FastAPI import
from fastapi import FastAPI

from .api import admin, auth as auth_router, configuration, queue
from .config import get_settings
from .migrations import run_migrations
from .queue import QueueWorker

del _compat

app = FastAPI(title="VideoReduce Backend", version="0.1.0")
settings = get_settings()
worker = QueueWorker()


@app.on_event("startup")
def startup_event() -> None:
    """Run migrations and start the background worker."""

    run_migrations()
    worker.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    """Stop the background worker gracefully."""

    worker.stop()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple health endpoint useful for monitoring."""

    return {"status": "ok"}


app.include_router(auth_router.router)
app.include_router(configuration.router)
app.include_router(queue.router)
app.include_router(admin.router)
