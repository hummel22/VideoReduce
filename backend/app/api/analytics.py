"""Endpoints powering dashboard analytics widgets."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..models import DashboardEvent, DashboardSnapshot, UserRole
from ..schemas import (
    DashboardEventCreate,
    DashboardEventResponse,
    DashboardSnapshotCreate,
    DashboardSnapshotResponse,
)
from . import deps

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=DashboardSnapshotResponse)
def get_overview(
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> DashboardSnapshotResponse:
    """Return the most recent dashboard metrics snapshot."""

    snapshot = (
        session.query(DashboardSnapshot)
        .order_by(DashboardSnapshot.recorded_at.desc())
        .first()
    )
    if snapshot is None:
        return DashboardSnapshotResponse(
            id=None,
            active_jobs=0,
            average_throughput_minutes=0.0,
            smb_latency_ms=0.0,
            storage_budget_bytes=0,
            recorded_at=datetime.utcnow(),
        )
    return DashboardSnapshotResponse.from_orm(snapshot)


@router.post(
    "/overview",
    response_model=DashboardSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_overview(
    payload: DashboardSnapshotCreate,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> DashboardSnapshotResponse:
    """Persist a new dashboard metrics snapshot."""

    snapshot = DashboardSnapshot(**payload.dict())
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return DashboardSnapshotResponse.from_orm(snapshot)


@router.get("/events", response_model=list[DashboardEventResponse])
def list_events(
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> list[DashboardEventResponse]:
    """Return timeline events ordered from newest to oldest."""

    events = session.query(DashboardEvent).order_by(DashboardEvent.created_at.desc()).all()
    return [DashboardEventResponse.from_orm(event) for event in events]


@router.post(
    "/events",
    response_model=DashboardEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    payload: DashboardEventCreate,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> DashboardEventResponse:
    """Record a new dashboard timeline event."""

    event = DashboardEvent(**payload.dict())
    session.add(event)
    session.commit()
    session.refresh(event)
    return DashboardEventResponse.from_orm(event)
