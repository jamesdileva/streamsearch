"""Background refresh tests (Sprint 4.3 verification).

Controlled test set, observing: refresh, ending, expiration, errors,
batching — plus the manual trigger shape. All isolated temp DBs.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.adapters.base import AdapterError, BasePlatformAdapter
from app.config import settings
from app.main import app
from app.models.stream import Stream
from app.services import index
from app.services.refresh import run_refresh_once

client = TestClient(app)

NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)
OLD = NOW - timedelta(hours=3)


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/r.db")


def _record(pid: str, **over) -> dict:
    base = {
        "id": pid,
        "platform": "stub",
        "platform_stream_id": pid,
        "title": "Stub live",
        "live_status": "live",
    }
    return {**base, **over}


class _LiveStub(BasePlatformAdapter):
    """Judges every id: live ones return records, the rest are gone."""

    platform = "stub"

    def __init__(self, live_ids: set[str]) -> None:
        self.live_ids = live_ids

    def search(self, query: str) -> list[dict]:
        return []

    def reverify(self, ids: list[str]) -> dict[str, dict | None]:
        return {
            pid: (_record(pid) if pid in self.live_ids else None) for pid in ids
        }


class _SilentStub(BasePlatformAdapter):
    """Unsupported reverify (inherits default {}) — records must age honestly."""

    platform = "silent"

    def search(self, query: str) -> list[dict]:
        return []


class _ExplodingStub(BasePlatformAdapter):
    platform = "boom"

    def search(self, query: str) -> list[dict]:
        return []

    def reverify(self, ids: list[str]) -> dict[str, dict | None]:
        raise AdapterError("quota exhausted")


def _seed(pid: str, platform: str = "stub", at: datetime = OLD, **over) -> None:
    rec = _record(pid, **over)
    rec["platform"] = platform
    index.upsert_stream(Stream(**rec), at)


def test_refresh_advances_last_seen(isolated_db):
    _seed("s1")
    report = run_refresh_once(adapters=[_LiveStub({"s1"})], now=NOW)
    assert (report.checked, report.refreshed, report.ended) == (1, 1, 0)
    stored = index.get_stream("stub", "s1")
    assert stored is not None
    assert stored.last_seen_at == NOW
    assert stored.live_status == "live"


def test_confirmed_gone_transitions_to_ended(isolated_db):
    _seed("gone")
    report = run_refresh_once(adapters=[_LiveStub(set())], now=NOW)
    assert (report.checked, report.refreshed, report.ended) == (1, 0, 1)
    stored = index.get_stream("stub", "gone")
    assert stored is not None
    assert stored.live_status == "ended"
    assert stored.ended_at == NOW


def test_unsupported_adapter_leaves_record_untouched(isolated_db):
    _seed("s1", platform="silent")
    report = run_refresh_once(adapters=[_SilentStub()], now=NOW)
    assert (report.checked, report.refreshed, report.ended) == (1, 0, 0)
    stored = index.get_stream("silent", "s1")
    assert stored is not None
    assert stored.live_status == "live"
    assert stored.last_seen_at == OLD


def test_reverify_error_recorded_others_continue(isolated_db):
    _seed("ok")
    _seed("bad", platform="boom")
    report = run_refresh_once(
        adapters=[_LiveStub({"ok"}), _ExplodingStub()], now=NOW
    )
    assert len(report.errors) == 1
    assert "boom" in report.errors[0]
    stored = index.get_stream("stub", "ok")
    assert stored is not None and stored.live_status == "live"


def test_batch_limit_respected(isolated_db):
    for pid in ("a", "b", "c"):
        _seed(pid)
    report = run_refresh_once(adapters=[_LiveStub({"a", "b", "c"})], batch_size=2)
    assert report.checked == 2
    assert report.refreshed == 2


def test_pass_prunes_old_ended(isolated_db):
    _seed("old", live_status="ended", at=NOW - timedelta(days=40))
    _seed("fresh")
    report = run_refresh_once(
        adapters=[_LiveStub({"fresh"})], prune_days=30, now=NOW
    )
    assert report.pruned == 1
    assert index.get_stream("stub", "old") is None


def test_trigger_endpoint_shape(isolated_db):
    body = client.post("/api/refresh").json()
    assert set(body) == {"checked", "refreshed", "ended", "pruned", "errors"}
    assert isinstance(body["errors"], list)
