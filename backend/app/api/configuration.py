"""Configuration endpoints for SMB and encoding details."""
from __future__ import annotations

import socket
import time
from typing import Tuple
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..models import EncodingRule, SMBConfig, SMBPreset, UserRole
from ..schemas import (
    EncodingRuleResponse,
    SMBConfigResponse,
    SMBConfigTestResponse,
    SMBConfigUpdateRequest,
    SMBPresetCreateRequest,
    SMBPresetResponse,
    SMBPresetUpdateRequest,
)
from . import deps

router = APIRouter(prefix="/config", tags=["config"])

_DEFAULT_SMB_PORT = 445


def _extract_host_and_port(share_url: str) -> Tuple[str, int]:
    """Return the host and port extracted from a share URL.

    The admin dashboard allows entering the share with a leading ``//``.  For
    parsing we normalise the value into an ``smb://`` URL so that
    :func:`urllib.parse.urlparse` can determine the host/port information.  The
    share path itself is irrelevant for the connectivity check – only the host
    and optional port are required.
    """

    candidate = share_url.strip()
    if not candidate:
        raise ValueError("Share URL must not be empty")

    if candidate.startswith("\\\\"):
        candidate = candidate.replace("\\", "/")

    if candidate.startswith("smb://"):
        normalised = candidate
    elif candidate.startswith("//"):
        normalised = f"smb:{candidate}"
    else:
        normalised = f"smb://{candidate.lstrip('/')}"

    parsed = urlparse(normalised)
    host = parsed.hostname
    if not host:
        raise ValueError("Unable to determine host from share URL")
    port = parsed.port or _DEFAULT_SMB_PORT
    return host, port


def _test_smb_connectivity(host: str, port: int, timeout: float = 3.0) -> SMBConfigTestResponse:
    """Attempt a TCP connection to the SMB share host and return timing info."""

    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency = (time.perf_counter() - start) * 1000
    except OSError as exc:
        latency = (time.perf_counter() - start) * 1000
        message = f"Unable to connect to {host}:{port}: {exc}"
        return SMBConfigTestResponse(success=False, message=message, latency_ms=round(latency, 2))

    message = f"Successfully connected to {host}:{port}."
    return SMBConfigTestResponse(success=True, message=message, latency_ms=round(latency, 2))


@router.get("/smb", response_model=SMBConfigResponse)
def get_smb_configuration(
    payload: dict = Depends(deps.require_roles(UserRole.MOBILE, UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> SMBConfigResponse:
    """Return the most recent SMB configuration."""

    config = session.query(SMBConfig).order_by(SMBConfig.updated_at.desc()).first()
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMB configuration missing")
    return SMBConfigResponse.from_orm(config)


@router.put("/smb", response_model=SMBConfigResponse)
def update_smb_configuration(
    payload: SMBConfigUpdateRequest,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> SMBConfigResponse:
    """Persist the SMB configuration for use by clients."""

    values = payload.dict()
    config = session.query(SMBConfig).order_by(SMBConfig.updated_at.desc()).first()
    if config is None:
        config = SMBConfig(**values)
        session.add(config)
    else:
        for field, value in values.items():
            setattr(config, field, value)

    session.commit()
    session.refresh(config)
    return SMBConfigResponse.from_orm(config)


@router.post("/smb/test", response_model=SMBConfigTestResponse)
def test_smb_configuration(
    payload: SMBConfigUpdateRequest,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
) -> SMBConfigTestResponse:
    """Attempt to reach the SMB share host using the provided configuration."""

    try:
        host, port = _extract_host_and_port(payload.share_url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _test_smb_connectivity(host, port)


def _get_smb_preset(session: Session, preset_id: int) -> SMBPreset:
    preset = session.query(SMBPreset).filter(SMBPreset.id == preset_id).one_or_none()
    if preset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found")
    return preset


@router.get("/smb/presets", response_model=list[SMBPresetResponse])
def list_smb_presets(
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> list[SMBPresetResponse]:
    """Return stored SMB presets for administrators."""

    presets = session.query(SMBPreset).order_by(SMBPreset.name.asc(), SMBPreset.id.asc()).all()
    return [SMBPresetResponse.from_orm(preset) for preset in presets]


@router.post(
    "/smb/presets",
    response_model=SMBPresetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_smb_preset(
    payload: SMBPresetCreateRequest,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> SMBPresetResponse:
    """Create a new SMB preset for reuse."""

    preset = SMBPreset(**payload.dict())
    session.add(preset)
    session.commit()
    session.refresh(preset)
    return SMBPresetResponse.from_orm(preset)


@router.put("/smb/presets/{preset_id}", response_model=SMBPresetResponse)
def update_smb_preset(
    preset_id: int,
    payload: SMBPresetUpdateRequest,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> SMBPresetResponse:
    """Update the fields of an existing SMB preset."""

    preset = _get_smb_preset(session, preset_id)
    for field, value in payload.dict().items():
        setattr(preset, field, value)
    session.commit()
    session.refresh(preset)
    return SMBPresetResponse.from_orm(preset)


@router.delete("/smb/presets/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_smb_preset(
    preset_id: int,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> Response:
    """Delete an SMB preset."""

    preset = _get_smb_preset(session, preset_id)
    session.delete(preset)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/encoding/rules", response_model=list[EncodingRuleResponse])
def list_encoding_rules(
    payload: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> list[EncodingRuleResponse]:
    """List encoding rules for administrative review."""

    rules = (
        session.query(EncodingRule)
        .order_by(EncodingRule.id)
        .all()
    )
    return [EncodingRuleResponse.from_orm(rule) for rule in rules]
