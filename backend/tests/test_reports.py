"""Reports tests: submit each type, verify persistence (Sprint 2.3)."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(
        settings, "database_url", f"sqlite:///{tmp_path}/reports.db"
    )


@pytest.mark.parametrize(
    "reason", ["broken_link", "no_longer_live", "wrong_topic", "other"]
)
def test_each_report_type_persists(isolated_db, reason: str):
    r = client.post(
        "/api/reports",
        json={"stream_id": "vid-1", "platform": "youtube", "reason": reason},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["id"] >= 1
    assert body["reason"] == reason
    assert body["stream_id"] == "vid-1"
    assert body["created_at"]

    listed = client.get("/api/reports").json()
    assert listed["count"] == 1
    assert listed["reports"][0]["reason"] == reason


def test_reports_list_filters_by_stream(isolated_db):
    client.post("/api/reports", json={"stream_id": "a", "reason": "broken_link"})
    client.post("/api/reports", json={"stream_id": "b", "reason": "other"})
    body = client.get("/api/reports", params={"stream_id": "a"}).json()
    assert body["count"] == 1
    assert body["reports"][0]["stream_id"] == "a"


def test_report_with_detail_round_trips(isolated_db):
    r = client.post(
        "/api/reports",
        json={"stream_id": "a", "reason": "other", "detail": "  off topic  "},
    )
    assert r.status_code == 201
    assert r.json()["detail"] == "off topic"


def test_bad_reason_is_422_envelope(isolated_db):
    r = client.post("/api/reports", json={"stream_id": "a", "reason": "spam"})
    assert r.status_code == 422


def test_empty_stream_id_is_422(isolated_db):
    r = client.post(
        "/api/reports", json={"stream_id": "  ", "reason": "broken_link"}
    )
    assert r.status_code == 422


def test_oversized_detail_is_422(isolated_db):
    r = client.post(
        "/api/reports",
        json={"stream_id": "a", "reason": "other", "detail": "x" * 501},
    )
    assert r.status_code == 422
