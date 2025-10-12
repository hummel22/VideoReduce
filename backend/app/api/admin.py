"""Administrative endpoints for managing API tokens."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..auth import ensure_user
from ..models import APIToken, UserRole
from ..schemas import CreateTokenRequest, CreateTokenResponse, TokenListResponse
from . import deps

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/tokens", response_model=CreateTokenResponse, status_code=status.HTTP_201_CREATED)
def create_token(
    payload: CreateTokenRequest,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> CreateTokenResponse:
    """Create or reuse a user and issue a new API token."""

    user = ensure_user(session, payload.username, UserRole.MOBILE)
    token_value = secrets.token_urlsafe(32)
    api_token = APIToken(user=user, token=token_value, description=payload.description)
    session.add(api_token)
    session.commit()
    session.refresh(api_token)
    return CreateTokenResponse(token=api_token.token, user_id=user.id, description=api_token.description)


@router.get("/tokens", response_model=list[TokenListResponse])
def list_tokens(
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> list[TokenListResponse]:
    """Return API tokens for auditing."""

    tokens = session.query(APIToken).order_by(APIToken.created_at.desc()).all()
    return [TokenListResponse.from_orm(item) for item in tokens]


@router.delete(
    "/tokens/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def revoke_token(
    token_id: int,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> Response:
    """Delete an API token."""

    token_obj = session.query(APIToken).filter(APIToken.id == token_id).one_or_none()
    if token_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    session.delete(token_obj)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
