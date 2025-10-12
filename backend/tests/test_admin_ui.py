"""Tests for the embedded Vue admin panel."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def test_admin_dashboard_index_served() -> None:
    """The index HTML should be served when the dashboard assets are present."""

    with TestClient(app) as client:
        response = client.get("/admin")
        assert response.status_code == 200
        assert "VideoReduce Admin Panel" in response.text

        asset_response = client.get("/admin/static/app.js")
        assert asset_response.status_code == 200
        assert "createApp" in asset_response.text
