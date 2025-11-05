"""Common FastAPI dependency utilities."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..auth import AuthenticationError, decode_token
from ..database import get_session
from ..models import UserRole

http_bearer = HTTPBearer(auto_error=False)


def get_current_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> dict:
    """Return the decoded JWT payload or raise an HTTP 401 error."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return payload


def require_roles(*roles: UserRole):
    """Create a dependency ensuring the current token is one of the allowed roles."""

    allowed_roles = {role.value for role in roles}

    def dependency(payload: dict = Depends(get_current_token)) -> dict:
        token_role = payload.get("role")
        if token_role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return payload

    return dependency


def require_role(role: UserRole):
    """Create a dependency that ensures the current token has the desired role."""

    return require_roles(role)


def get_db_session(session: Session = Depends(get_session)) -> Session:
    """Expose the SQLAlchemy session as a dependency."""

    return session
