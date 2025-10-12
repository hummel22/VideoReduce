"""FastAPI application entry point."""
from __future__ import annotations

from . import compat as _compat  # noqa: F401  # Ensure compatibility patches run before FastAPI import
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api import admin, auth as auth_router, configuration, queue
from .config import get_settings
from .migrations import run_migrations
from .queue import QueueWorker

del _compat

app = FastAPI(title="VideoReduce Backend", version="0.1.0")
settings = get_settings()
worker = QueueWorker()

ADMIN_UI_DIR = Path(__file__).resolve().parent / "admin_ui"
ADMIN_ASSETS_DIR = ADMIN_UI_DIR / "assets"

if ADMIN_ASSETS_DIR.exists():
    app.mount(
        "/admin/static",
        StaticFiles(directory=ADMIN_ASSETS_DIR),
        name="admin-static",
    )


def _load_admin_index() -> str:
    if not ADMIN_UI_DIR.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin panel is not available.",
        )
    index_path = ADMIN_UI_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin panel build is missing.",
        )
    return index_path.read_text(encoding="utf-8")


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


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
@app.get("/admin/", response_class=HTMLResponse, include_in_schema=False)
def admin_panel() -> HTMLResponse:
    """Serve the Vue-based administrative dashboard."""

    return HTMLResponse(_load_admin_index())


app.include_router(auth_router.router)
app.include_router(configuration.router)
app.include_router(queue.router)
app.include_router(admin.router)
