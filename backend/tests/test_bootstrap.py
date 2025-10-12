"""Tests for bootstrapping static dashboard credentials."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.bootstrap import ensure_dashboard_service_account
from backend.app.migrations import apply_migrations
from backend.app.models import APIToken, User, UserRole


def test_ensure_dashboard_service_account(tmp_path):
    db_path = tmp_path / "bootstrap.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)

    with Session() as session:
        apply_migrations(session)

    with Session() as session:
        ensure_dashboard_service_account(
            session,
            username="dashboard-test",
            token_value="static-dashboard-token",
        )
        session.commit()

    with Session() as session:
        user = session.query(User).filter(User.username == "dashboard-test").one()
        assert user.role == UserRole.ADMIN.value
        token = session.query(APIToken).filter(APIToken.token == "static-dashboard-token").one()
        assert token.user_id == user.id

        # Simulate manual changes and ensure the bootstrapper corrects them on the next run.
        another_user = User(username="other", password="", role=UserRole.MOBILE.value)
        session.add(another_user)
        session.flush()
        token.user = another_user
        user.role = UserRole.MOBILE.value
        session.commit()

    with Session() as session:
        ensure_dashboard_service_account(
            session,
            username="dashboard-test",
            token_value="static-dashboard-token",
        )
        session.commit()

    with Session() as session:
        user = session.query(User).filter(User.username == "dashboard-test").one()
        token = session.query(APIToken).filter(APIToken.token == "static-dashboard-token").one()
        assert user.role == UserRole.ADMIN.value
        assert token.user_id == user.id
