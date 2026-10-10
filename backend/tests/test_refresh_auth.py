"""Refresh-trigger auth tests (hardening sprint after 10.2).

The manual `/api/refresh` spends platform quota, so it must be fail-closed:
unconfigured means disabled, and a wrong token is rejected identically to
a missing one. The background loop is untouched and needs no credentials.
"""

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

TOKEN = "test-refresh-token"


def test_missing_configuration_disables_endpoint(monkeypatch):
    monkeypatch.setattr(settings, "refresh_token", "")
    r = client.post("/api/refresh")
    assert r.status_code == 503
    assert r.json() == {
        "error": {"code": 503, "message": "refresh endpoint is not configured"}
    }


def test_valid_token_allows_refresh(monkeypatch):
    monkeypatch.setattr(settings, "refresh_token", TOKEN)
    r = client.post("/api/refresh", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200
    body = r.json()
    assert {"checked", "refreshed", "ended", "pruned", "errors"} <= set(body)


def test_wrong_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "refresh_token", TOKEN)
    r = client.post("/api/refresh", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401
    assert "invalid" in r.json()["error"]["message"]
    assert r.headers.get("www-authenticate") == "Bearer"


def test_missing_authorization_header_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "refresh_token", TOKEN)
    r = client.post("/api/refresh")
    assert r.status_code == 401


def test_malformed_authorization_header_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "refresh_token", TOKEN)
    r = client.post("/api/refresh", headers={"Authorization": TOKEN})
    assert r.status_code == 401


def test_token_leak_check_public_endpoints(monkeypatch):
    """No other endpoint may require or accept this token by accident."""
    monkeypatch.setattr(settings, "refresh_token", TOKEN)
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/stats").status_code == 200
    # Search stays open for users; the token guards quota-spending ops only.
    assert client.get("/api/search", params={"q": "storm"}).status_code in (200, 502)
