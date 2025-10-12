"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth
from ..auth import AuthenticationError
from ..database import get_session
from ..schemas import (
    LoginRequest,
    MobileTokenRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate an administrator using environment credentials."""

    try:
        token, expires_in = auth.authenticate_admin(payload.username, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post("/mobile", response_model=TokenResponse)
def login_mobile(
    payload: MobileTokenRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Authenticate a mobile client using an API token."""

    try:
        token, expires_in = auth.authenticate_mobile(session, payload.token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=token, expires_in=expires_in)
