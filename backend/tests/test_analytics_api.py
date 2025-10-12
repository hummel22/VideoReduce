"""Integration tests covering dashboard analytics and user APIs."""
from __future__ import annotations

from backend.app.config import get_settings


def _auth_headers(client):
    response = client.post(
        "/api/auth/mobile",
        json={"token": get_settings().dashboard_token},
    )
    payload = response.json()
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_analytics_overview_defaults(api_client):
    headers = _auth_headers(api_client)

    response = api_client.get("/api/analytics/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active_jobs"] == 0
    assert data["average_throughput_minutes"] == 0
    assert data["smb_latency_ms"] == 0
    assert data["storage_budget_bytes"] == 0

    snapshot = {
        "active_jobs": 3,
        "average_throughput_minutes": 54.5,
        "smb_latency_ms": 112.2,
        "storage_budget_bytes": 987654321,
    }
    create_response = api_client.post(
        "/api/analytics/overview",
        json=snapshot,
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["active_jobs"] == snapshot["active_jobs"]

    latest_response = api_client.get("/api/analytics/overview", headers=headers)
    latest = latest_response.json()
    assert latest["average_throughput_minutes"] == snapshot["average_throughput_minutes"]
    assert latest["smb_latency_ms"] == snapshot["smb_latency_ms"]
    assert latest["storage_budget_bytes"] == snapshot["storage_budget_bytes"]



def test_analytics_events_round_trip(api_client):
    headers = _auth_headers(api_client)

    response = api_client.get("/api/analytics/events", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

    first = api_client.post(
        "/api/analytics/events",
        json={"title": "Queue cleared", "description": "Queue back to zero."},
        headers=headers,
    ).json()
    second = api_client.post(
        "/api/analytics/events",
        json={
            "title": "New upload",
            "description": "Uploaded demo clip",
        },
        headers=headers,
    ).json()

    events = api_client.get("/api/analytics/events", headers=headers).json()
    titles = [event["title"] for event in events]
    assert titles == [second["title"], first["title"]]



def test_user_token_creation(api_client):
    headers = _auth_headers(api_client)

    list_response = api_client.get("/api/users", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    payload = {"username": "camera-1"}
    create_response = api_client.post("/api/users", json=payload, headers=headers)
    assert create_response.status_code == 201
    data = create_response.json()
    assert data["username"] == payload["username"]
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 10

    list_after = api_client.get("/api/users", headers=headers).json()
    assert len(list_after) == 1
    assert list_after[0]["username"] == payload["username"]
    assert list_after[0]["token"] == data["token"]
    assert "created_at" in list_after[0]
