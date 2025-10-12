"""Queue management endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import JobEvent, QueueJob, QueueStage, UserRole
from ..schemas import (
    JobEventResponse,
    QueueJobCreate,
    QueueJobDetailResponse,
    QueueJobResponse,
    QueueProgressResponse,
)
from . import deps

router = APIRouter(prefix="/queue", tags=["queue"])
settings = get_settings()


@router.post("/jobs", response_model=QueueJobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: QueueJobCreate,
    token: dict = Depends(deps.require_role(UserRole.MOBILE)),
    session: Session = Depends(deps.get_db_session),
) -> QueueJobResponse:
    """Create a queue job using API metadata."""

    existing = session.query(QueueJob).filter(QueueJob.video_name == payload.video_name).one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job already exists")
    source_path = Path(settings.input_dir) / payload.video_name
    manifest_path = Path(settings.input_dir) / f"{Path(payload.video_name).stem}.json"
    job = QueueJob(
        video_name=payload.video_name,
        source_path=str(source_path),
        manifest_path=str(manifest_path),
        requested_profile=payload.requested_profile,
        high_quality=payload.high_quality,
        file_size_mb=payload.file_size_mb,
        duration_seconds=payload.duration_seconds,
        resolution_height=payload.resolution_height,
    )
    session.add(job)
    session.add(JobEvent(job=job, event_type="queued", message="Queued via API"))
    session.commit()
    session.refresh(job)
    return QueueJobResponse.from_orm(job)


@router.get("/jobs", response_model=list[QueueJobResponse])
def list_jobs(
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> list[QueueJobResponse]:
    """List all queue jobs for administrative review."""

    jobs = session.query(QueueJob).order_by(QueueJob.created_at.desc()).all()
    return [QueueJobResponse.from_orm(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=QueueJobDetailResponse)
def get_job(
    job_id: int,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> QueueJobDetailResponse:
    """Return details and events for a specific job."""

    job = session.query(QueueJob).filter(QueueJob.id == job_id).one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return QueueJobDetailResponse(
        **QueueJobResponse.from_orm(job).dict(),
        events=[JobEventResponse.from_orm(event) for event in job.events],
    )


@router.get("/progress/{video_name}", response_model=QueueProgressResponse)
def get_progress(
    video_name: str,
    token: dict = Depends(deps.require_role(UserRole.MOBILE)),
    session: Session = Depends(deps.get_db_session),
) -> QueueProgressResponse:
    """Return the progress for a job identified by its video name."""

    job = session.query(QueueJob).filter(QueueJob.video_name == video_name).one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return QueueProgressResponse(
        video_name=job.video_name,
        progress=job.progress,
        status=job.status,
        stage=QueueStage(job.stage),
    )
