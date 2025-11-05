"""Tests for the configuration API endpoints."""
from __future__ import annotations

from backend.app.config import get_settings


def _auth_headers(client):
    response = client.post(
        "/api/auth/mobile",
        json={"token": get_settings().dashboard_token},
    )
    payload = response.json()
    return {"Authorization": f"Bearer {payload['access_token']}"}


def _sample_payload():
    return {
        "share_url": "//storage.local/VideoReduce",
        "username": "transcode",
        "password": "secret",
        "input_path": "/input",
        "output_path": "/output",
    }


def _preset_payload(**overrides):
    payload = {
        "name": "Studio NAS",
        "description": "Primary storage array.",
        "share_url": "//nas.local/VideoReduce",
        "username": "studio",
        "password": "s3cret",
        "input_path": "/incoming",
        "output_path": "/processed",
    }
    payload.update(overrides)
    return payload


def test_get_smb_configuration_seeded(api_client):
    headers = _auth_headers(api_client)

    response = api_client.get("/api/config/smb", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["share_url"] == "smb://localhost/videos"
    assert data["input_path"] == "/input"
    assert data["output_path"] == "/output"
    assert data["username"] == "demo"
    assert data["password"] == "demo"


def test_update_and_fetch_smb_configuration(api_client):
    headers = _auth_headers(api_client)
    payload = _sample_payload()

    save_response = api_client.put("/api/config/smb", json=payload, headers=headers)
    assert save_response.status_code == 200
    saved = save_response.json()
    for key, value in payload.items():
        assert saved[key] == value

    fetch_response = api_client.get("/api/config/smb", headers=headers)
    assert fetch_response.status_code == 200
    fetched = fetch_response.json()
    assert fetched == saved


def test_smb_configuration_test_success(api_client, monkeypatch):
    headers = _auth_headers(api_client)

    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    captured = {}

    def fake_create_connection(address, timeout=3.0):  # pragma: no cover - patched during tests
        captured["address"] = address
        captured["timeout"] = timeout
        return DummyConnection()

    monkeypatch.setattr(
        "backend.app.api.configuration.socket.create_connection",
        fake_create_connection,
    )

    response = api_client.post(
        "/api/config/smb/test",
        json=_sample_payload(),
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "storage.local" in captured["address"][0]
    assert captured["timeout"] == 3.0


def test_smb_configuration_test_failure(api_client, monkeypatch):
    headers = _auth_headers(api_client)

    def fake_create_connection(address, timeout=3.0):  # pragma: no cover - patched during tests
        raise OSError("unreachable")

    monkeypatch.setattr(
        "backend.app.api.configuration.socket.create_connection",
        fake_create_connection,
    )

    response = api_client.post(
        "/api/config/smb/test",
        json=_sample_payload(),
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "unreachable" in data["message"]
    assert data["latency_ms"] >= 0


def test_list_smb_presets_initially_empty(api_client):
    headers = _auth_headers(api_client)

    response = api_client.get("/api/config/smb/presets", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_update_and_delete_smb_preset(api_client):
    headers = _auth_headers(api_client)
    create_response = api_client.post(
        "/api/config/smb/presets",
        json=_preset_payload(),
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Studio NAS"
    assert created["description"] == "Primary storage array."
    assert created["share_url"] == "//nas.local/VideoReduce"

    list_response = api_client.get("/api/config/smb/presets", headers=headers)
    assert list_response.status_code == 200
    presets = list_response.json()
    assert len(presets) == 1
    assert presets[0]["id"] == created["id"]

    update_response = api_client.put(
        f"/api/config/smb/presets/{created['id']}",
        json=_preset_payload(
            name="Studio NAS Mirror",
            description=None,
            share_url="//nas.backup/VideoReduce",
            input_path="/mirror/in",
            output_path="/mirror/out",
            username="backup",
            password="mirror",
        ),
        headers=headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Studio NAS Mirror"
    assert updated["description"] is None
    assert updated["share_url"] == "//nas.backup/VideoReduce"
    assert updated["username"] == "backup"
    assert updated["password"] == "mirror"
    assert updated["input_path"] == "/mirror/in"
    assert updated["output_path"] == "/mirror/out"

    delete_response = api_client.delete(
        f"/api/config/smb/presets/{created['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 204

    final_list = api_client.get("/api/config/smb/presets", headers=headers)
    assert final_list.status_code == 200
    assert final_list.json() == []


def test_update_missing_smb_preset_returns_not_found(api_client):
    headers = _auth_headers(api_client)

    response = api_client.put(
        "/api/config/smb/presets/9999",
        json=_preset_payload(name="Missing"),
        headers=headers,
    )
    assert response.status_code == 404


def test_delete_missing_smb_preset_returns_not_found(api_client):
    headers = _auth_headers(api_client)

    response = api_client.delete(
        "/api/config/smb/presets/9999",
        headers=headers,
    )
    assert response.status_code == 404
