"""Persistent index tests (Sprint 4.2 verification).

No duplicates, metadata overwrites, ended transitions, old-record removal —
each against an isolated temp database. Service population is covered too.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.base import BasePlatformAdapter
from app.config import settings
from app.models.stream import Stream
from app.services import index
from app.services.cache import SearchCache
from app.services.search import SearchService

NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/idx.db")


def _stream(**over) -> Stream:
    base = {
        "id": "youtube-v1",
        "platform": "youtube",
        "platform_stream_id": "v1",
        "channel_name": "Chan",
        "title": "Live now",
        "live_status": "live",
        "freshness": "fresh",
        "viewer_count": 10,
        "tags": ["news"],
        "latitude": 34.05,
        "metadata": {"k": "v"},
    }
    return Stream(**{**base, **over})


def test_repeat_upsert_creates_no_duplicates(isolated_db):
    first = index.upsert_stream(_stream(), NOW)
    second = index.upsert_stream(_stream(), NOW + timedelta(minutes=5))
    assert index.index_counts() == (1, 1)
    assert second.first_seen_at == first.first_seen_at
    assert second.last_seen_at and first.last_seen_at
    assert second.last_seen_at > first.last_seen_at


def test_updated_metadata_overwrites(isolated_db):
    index.upsert_stream(_stream(), NOW)
    stored = index.upsert_stream(
        _stream(title="New title", viewer_count=99, tags=["a", "b"]), NOW
    )
    assert stored.title == "New title"
    assert stored.viewer_count == 99
    assert stored.tags == ["a", "b"]
    assert index.index_counts() == (1, 1)


def test_live_to_ended_transition_sets_ended_at(isolated_db):
    live = index.upsert_stream(_stream(), NOW)
    assert live.ended_at is None
    ended = index.upsert_stream(
        _stream(live_status="ended", freshness="ended"), NOW + timedelta(hours=1)
    )
    assert ended.ended_at is not None
    assert ended.live_status == "ended"
    # A second ended sighting keeps the original transition time.
    again = index.upsert_stream(
        _stream(live_status="ended", freshness="ended"), NOW + timedelta(hours=2)
    )
    assert again.ended_at == ended.ended_at


def test_relive_clears_ended_at(isolated_db):
    index.upsert_stream(_stream(live_status="ended"), NOW)
    relive = index.upsert_stream(_stream(live_status="live"), NOW)
    assert relive.ended_at is None
    assert index.index_counts() == (1, 1)


def test_get_and_list_round_trip_types(isolated_db):
    index.upsert_stream(_stream(), NOW)
    stored = index.get_stream("youtube", "v1")
    assert stored is not None
    assert stored.latitude == 34.05
    assert stored.metadata == {"k": "v"}
    assert stored.first_seen_at is not None
    assert index.get_stream("youtube", "missing") is None
    assert [s.id for s in index.list_streams()] == ["youtube-v1"]
    assert index.list_streams(live_status="ended") == []


def test_prune_removes_only_old_ended(isolated_db):
    old = NOW - timedelta(days=40)
    index.upsert_stream(_stream(id="old-ended", platform_stream_id="oe",
                                live_status="ended"), old)
    index.upsert_stream(_stream(id="new-ended", platform_stream_id="ne",
                                live_status="ended"), NOW)
    index.upsert_stream(_stream(id="old-live", platform_stream_id="ol",
                                live_status="live"), old)
    assert index.prune_ended_older_than(30, NOW) == 1
    remaining = sorted(s.platform_stream_id for s in index.list_streams())
    assert remaining == ["ne", "ol"]


class _StubAdapter(BasePlatformAdapter):
    platform = "stub"

    def search(self, query: str) -> list[dict]:
        return [{
            "id": "stub-1", "platform": "stub", "platform_stream_id": "s1",
            "title": f"Hit for {query}", "live_status": "live",
        }]


def test_search_populates_index_without_duplicates(isolated_db):
    service = SearchService(
        adapters=[_StubAdapter()], cache=SearchCache(ttl_seconds=60)
    )
    service.search("wildfire")
    service.search("wildfire")  # cache hit: no second write
    service.search("storm")  # same record id, new last_seen
    assert index.index_counts() == (1, 1)
    stored = index.get_stream("stub", "s1")
    assert stored is not None
    assert stored.last_seen_at is not None
