"""Startup helpers for seeding static service accounts."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .config import get_settings
from .database import session_scope
from .models import APIToken, User, UserRole


def ensure_dashboard_service_account(
    session: Session,
    *,
    username: Optional[str] = None,
    token_value: Optional[str] = None,
) -> None:
    """Ensure the static dashboard service account and token exist."""

    settings = get_settings()
    account_username = username or settings.dashboard_username
    api_token_value = token_value or settings.dashboard_token

    user = session.query(User).filter(User.username == account_username).one_or_none()
    if user is None:
        user = User(username=account_username, password="", role=UserRole.ADMIN.value)
        session.add(user)
        session.flush()
    elif user.role != UserRole.ADMIN.value:
        user.role = UserRole.ADMIN.value

    token = session.query(APIToken).filter(APIToken.token == api_token_value).one_or_none()
    if token is None:
        token = APIToken(
            token=api_token_value,
            description="Dashboard service token",
            user=user,
        )
        session.add(token)
    else:
        token.user = user
        if token.description != "Dashboard service token":
            token.description = "Dashboard service token"

    session.flush()


def bootstrap_service_accounts() -> None:
    """Create service accounts required for the application to run."""

    with session_scope() as session:
        ensure_dashboard_service_account(session)
