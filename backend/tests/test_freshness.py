"""Freshness simulations (Sprint 2.2 verification).

Each scenario from the roadmap — fresh stream, stream ending, failed
verification (record outlives its check), delayed API response (old
timestamp) — is a controlled record with a fixed clock. Periodic
revalidation itself lands in Sprint 4.3; this suite pins the labels.
"""

from datetime import datetime, timedelta, timezone

from app.adapters.base import FakeAdapter
from app.config import settings
from app.models.stream import Stream
from app.services.freshness import freshness_of
from app.services.search import SearchService

NOW = datetime(2026, 10, 4, tzinfo=timezone.utc)


def _stream(verified_ago=None, status="live") -> Stream:
    verified = NOW - verified_ago if verified_ago is not None else None
    return Stream(
        id="s",
        platform="fake",
        platform_stream_id="s",
        live_status=status,
        last_verified_at=verified,
    )


def test_fresh_stream():
    assert freshness_of(_stream(timedelta(seconds=60)), NOW) == "fresh"


def test_fresh_boundary_is_inclusive():
    assert freshness_of(_stream(timedelta(seconds=300)), NOW, 300, 1800) == "fresh"
    assert freshness_of(_stream(timedelta(seconds=301)), NOW, 300, 1800) == "aging"


def test_aging_stream():
    assert freshness_of(_stream(timedelta(minutes=10)), NOW) == "aging"


def test_aging_boundary_is_inclusive():
    assert freshness_of(_stream(timedelta(seconds=1800)), NOW, 300, 1800) == "aging"
    assert freshness_of(_stream(timedelta(seconds=1801)), NOW, 300, 1800) == "stale"


def test_stale_stream_delayed_response():
    assert freshness_of(_stream(timedelta(hours=2)), NOW) == "stale"


def test_never_verified_is_stale():
    assert freshness_of(_stream(None), NOW) == "stale"


def test_ended_stream_is_ended_despite_fresh_check():
    assert freshness_of(_stream(timedelta(seconds=10), "ended"), NOW) == "ended"


def test_future_timestamp_from_clock_skew_is_fresh():
    ahead = _stream(timedelta(seconds=-30))
    assert freshness_of(ahead, NOW) == "fresh"


def test_custom_thresholds_respected():
    assert freshness_of(_stream(timedelta(seconds=600)), NOW, 900, 3600) == "fresh"
    assert freshness_of(_stream(timedelta(seconds=600)), NOW, 300, 300) == "stale"


def test_config_threshold_defaults():
    assert settings.freshness_fresh_seconds == 300
    assert settings.freshness_aging_seconds == 1800


def test_service_stamps_freshness_on_results():
    res = SearchService(adapters=[FakeAdapter()]).search("wildfire")
    assert res.count == 1
    assert res.results[0].freshness == "fresh"
