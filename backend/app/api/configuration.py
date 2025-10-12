"""Configuration endpoints for SMB and encoding details."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models import EncodingRule, SMBConfig, UserRole
from ..schemas import EncodingRuleResponse, SMBConfigResponse
from . import deps

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/smb", response_model=SMBConfigResponse)
def get_smb_configuration(
    payload: dict = Depends(deps.require_role(UserRole.MOBILE)),
    session: Session = Depends(deps.get_db_session),
) -> SMBConfigResponse:
    """Return the most recent SMB configuration."""

    config = session.query(SMBConfig).order_by(SMBConfig.updated_at.desc()).first()
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMB configuration missing")
    return SMBConfigResponse.from_orm(config)


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
