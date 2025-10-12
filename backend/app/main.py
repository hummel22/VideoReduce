"""FastAPI application entry point."""
from __future__ import annotations

from pathlib import Path

from . import compat as _compat  # noqa: F401  # Ensure compatibility patches run before FastAPI import
from fastapi import APIRouter, FastAPI
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
api_router = APIRouter(prefix="/api")


@app.on_event("startup")
def startup_event() -> None:
    """Run migrations and start the background worker."""

    run_migrations()
    worker.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    """Stop the background worker gracefully."""

    worker.stop()


@api_router.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple health endpoint useful for monitoring."""

    return {"status": "ok"}


api_router.include_router(auth_router.router)
api_router.include_router(configuration.router)
api_router.include_router(queue.router)
api_router.include_router(admin.router)

app.include_router(api_router)


frontend_dist_dir = Path(__file__).resolve().parent / "static" / "frontend"
if frontend_dist_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")
else:

    @app.get("/", include_in_schema=False)
    def frontend_placeholder() -> HTMLResponse:
        """Return a helpful message when the frontend bundle is unavailable."""

        return HTMLResponse(
            "<h1>VideoReduce API</h1><p>The frontend bundle is not built. Run npm run build inside"
            " the frontend workspace.</p>",
            status_code=200,
        )
