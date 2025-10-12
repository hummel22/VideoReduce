"""Administrative endpoints for provisioning API users."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..auth import ensure_user
from ..models import APIToken, User, UserRole
from ..schemas import CreateUserRequest, CreateUserResponse, UserTokenResponse
from . import deps

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_token_response(token: APIToken) -> UserTokenResponse:
    user = token.user
    username = user.username if isinstance(user, User) else token.user.username  # pragma: no cover
    return UserTokenResponse(
        id=token.id,
        username=username,
        token=token.token,
        created_at=token.created_at,
    )


@router.get("", response_model=list[UserTokenResponse])
def list_user_tokens(
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> list[UserTokenResponse]:
    """Return API tokens issued to dashboard-managed users."""

    tokens = (
        session.query(APIToken)
        .join(User)
        .filter(User.role == UserRole.MOBILE.value)
        .order_by(APIToken.created_at.desc())
        .all()
    )
    return [_to_user_token_response(item) for item in tokens]


@router.post("", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
def create_user_token(
    payload: CreateUserRequest,
    token: dict = Depends(deps.require_role(UserRole.ADMIN)),
    session: Session = Depends(deps.get_db_session),
) -> CreateUserResponse:
    """Provision a user and return a freshly generated API token."""

    user = ensure_user(session, payload.username, UserRole.MOBILE)
    token_value = secrets.token_urlsafe(32)
    api_token = APIToken(user=user, token=token_value)
    session.add(api_token)
    session.commit()
    session.refresh(api_token)
    return _to_user_token_response(api_token)
