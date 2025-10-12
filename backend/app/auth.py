"""Authentication helpers including JWT issuance and validation."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import get_settings
from .models import APIToken, User, UserRole

settings = get_settings()


class AuthenticationError(Exception):
    """Raised when authentication cannot be completed."""


def create_access_token(subject: str, role: UserRole) -> tuple[str, int]:
    """Create a signed JWT for the given subject and role."""

    expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
    expire = datetime.utcnow() + expires_delta
    payload = {"sub": subject, "role": role.value, "exp": expire}
    encoded_jwt = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt, int(expires_delta.total_seconds())


def decode_token(token: str) -> dict[str, str]:
    """Decode and validate a JWT, returning its payload."""

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - jose already tested
        raise AuthenticationError("Invalid token") from exc
    return payload


def authenticate_admin(username: str, password: str) -> tuple[str, int]:
    """Validate administrator credentials sourced from the environment."""

    if username != settings.admin_username or password != settings.admin_password:
        raise AuthenticationError("Invalid administrator credentials")
    return create_access_token(subject=username, role=UserRole.ADMIN)


def authenticate_mobile(session: Session, token_value: str) -> tuple[str, int]:
    """Validate a mobile API token and issue a session JWT."""

    token = session.query(APIToken).filter(APIToken.token == token_value).one_or_none()
    if token is None:
        raise AuthenticationError("Unknown API token")
    token.last_used_at = datetime.utcnow()
    session.add(token)
    user = token.user
    return create_access_token(subject=str(user.id), role=UserRole(user.role))


def ensure_user(session: Session, username: str, role: UserRole) -> User:
    """Return an existing user or create one with the supplied role."""

    user = session.query(User).filter(User.username == username).one_or_none()
    if user:
        return user
    user = User(username=username, password="", role=role.value)
    session.add(user)
    session.flush()
    return user
