"""Observability tests (Sprint 10.3).

The roadmap's eight tracked quantities, each asserted end-to-end through the
real search path rather than poked in isolation: searches, cache hits,
adapter latency, adapter failures, streams discovered, stale streams,
report volume, and API quota estimate.
"""

import pytest

from app.adapters.base import AdapterError, BasePlatformAdapter
from app.config import settings
from app.models.report import ReportCreate
from app.services import index, metrics, reports
from app.services.cache import SearchCache
from app.services.metrics import MetricsRegistry, observability_snapshot
from app.services.search import SearchService


class _SlowHealthy(BasePlatformAdapter):
    platform = "slow"

    def search(self, query: str) -> list[dict]:
        return [
            {
                "id": "s-1",
                "platform": self.platform,
                "platform_stream_id": "s-1",
                "channel_name": "Chan",
                "title": "First record",
                "live_status": "live",
            },
            {
                "id": "s-2",
                "platform": self.platform,
                "platform_stream_id": "s-2",
                "channel_name": "Chan",
                "title": "Second record",
                "live_status": "live",
            },
        ]


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    # Index + report stores must be per-test: the discovery signal
    # (first_seen_at == last_seen_at) only holds against an empty table.
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/obs.db")


def _service(adapter, ttl: int = 60) -> SearchService:
    metrics.get_metrics().reset()
    return SearchService(adapters=[adapter], cache=SearchCache(ttl_seconds=ttl))


def test_searches_and_cache_metrics_tracked():
    service = _service(_SlowHealthy())
    service.search("storm")
    service.search("storm")  # cache hit
    snap = metrics.get_metrics().snapshot()
    assert snap["searches"] == 2
    assert snap["cache_hits"] == 1
    assert snap["cache_misses"] == 1
    assert snap["cache_hit_rate"] == 0.5


def test_adapter_latency_tracked_per_platform():
    service = _service(_SlowHealthy())
    service.search("storm")
    (entry,) = metrics.get_metrics().snapshot()["adapters"].values()
    assert entry["requests"] == 1
    assert entry["errors"] == 0
    assert entry["avg_latency_ms"] >= 0.0
    assert entry["last_latency_ms"] >= 0.0


def test_adapter_failures_tracked():
    class _Boom(BasePlatformAdapter):
        platform = "boom"

        def search(self, query: str) -> list[dict]:
            raise AdapterError("quota exhausted (403)")

    service = _service(_Boom())
    service.search("storm")
    (entry,) = metrics.get_metrics().snapshot()["adapters"].values()
    assert entry["errors"] == 1
    assert entry["last_error"] == "quota exhausted (403)"
    snap = metrics.get_metrics().snapshot()
    assert snap["adapter_errors"] == 1
    assert snap["adapter_error_rate"] == 1.0


def test_streams_discovered_vs_reindexed():
    service = _service(_SlowHealthy())
    service.search("storm")  # 2 new
    service.search("storm")  # cache hit, no writes
    service.search("hail")  # cache miss, re-sighting same 2
    snap = metrics.get_metrics().snapshot()
    assert snap["streams_discovered"] == 2  # genuinely new records
    assert snap["streams_indexed"] == 4  # 2 first-seen + 2 re-sightings


def test_api_requests_and_quota_estimate():
    class _Costly(BasePlatformAdapter):
        platform = "costly"
        search_quota_cost = 101

        def search(self, query: str) -> list[dict]:
            return []

    service = _service(_Costly())
    service.search("a")
    service.search("b")
    snap = metrics.get_metrics().snapshot()
    assert snap["api_requests"] == 2
    assert snap["estimated_quota_units"] == 202


def test_quota_estimate_excludes_request_limited_platforms():
    # Twitch/Kick declare 0: request-limited, not quota-limited.
    from app.adapters.fake_twitch import FakeTwitchAdapter

    service = _service(FakeTwitchAdapter())
    service.search("x")
    assert metrics.get_metrics().snapshot()["estimated_quota_units"] == 0
    assert metrics.get_metrics().snapshot()["api_requests"] == 1


def test_stale_and_unverified_index_metrics():
    from datetime import datetime, timedelta, timezone

    old = datetime.now(timezone.utc) - timedelta(hours=5)
    fresh = datetime.now(timezone.utc)
    index.upsert_stream(
        _record("fresh-1", verified=fresh, live="live"), fresh
    )
    index.upsert_stream(
        _record("stale-1", verified=old, live="live"), old
    )
    index.upsert_stream(
        _record("ended-1", verified=old, live="ended"), old
    )
    stats = index.index_stats(
        fresh_seconds=300, aging_seconds=1800, now=datetime.now(timezone.utc)
    )
    assert stats["total"] == 3
    assert stats["live"] == 2
    assert stats["ended"] == 1
    assert stats["fresh"] == 1
    assert stats["stale"] == 1
    assert stats["unverified"] == 0


def _record(pid: str, verified, live: str):
    from app.adapters.base import FakeAdapter

    (raw,) = FakeAdapter().search("x")
    raw.update(
        {
            "id": pid,
            "platform_stream_id": pid,
            "live_status": live,
            "last_verified_at": verified.isoformat(),
        }
    )
    from app.models.stream import Stream

    return Stream(**raw)


def test_report_volume_tracked():
    assert reports.count_reports() == 0
    reports.save_report(
        ReportCreate(stream_id="a", platform="fake", reason="broken_link")
    )
    reports.save_report(
        ReportCreate(stream_id="b", platform="fake", reason="other")
    )
    assert reports.count_reports() == 2


def test_observability_snapshot_composes_everything():
    service = _service(_SlowHealthy())
    service.search("storm")
    reports.save_report(
        ReportCreate(stream_id="a", platform="fake", reason="wrong_topic")
    )
    snapshot = observability_snapshot()
    assert snapshot["index"]["total"] == 2
    assert snapshot["reports"]["count"] == 1
    assert snapshot["live"]["searches"] == 1
    assert snapshot["live"]["streams_discovered"] == 2


def test_registry_reset_clears_everything():
    registry = MetricsRegistry()
    registry.record_search_started()
    registry.record_cache_hit()
    registry.record_adapter_success("x", 1.0)
    registry.record_adapter_error("x", "err")
    registry.record_index_write(discovered=True)
    registry.add_quota_estimate(50)
    registry.reset()
    snap = registry.snapshot()
    assert snap["searches"] == 0
    assert snap["cache_hits"] == 0
    assert snap["api_requests"] == 0
    assert snap["streams_discovered"] == 0
    assert snap["estimated_quota_units"] == 0
    assert snap["adapters"] == {}


def test_observability_survives_report_store_failure(tmp_path, monkeypatch):
    """A broken report store must not break the dashboard it feeds."""
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/ok.db")
    monkeypatch.setattr(reports, "count_reports", lambda: (_ for _ in ()).throw(OSError("disk")))
    snapshot = observability_snapshot()
    assert snapshot["reports"]["count"] == -1
    assert snapshot["index"]["total"] >= 0
