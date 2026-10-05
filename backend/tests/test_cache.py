"""Result caching tests (Sprint 4.1 verification).

The roadmap check — run the same search repeatedly and confirm the
platform isn't queried unnecessarily — is a counting adapter here, plus a
live two-request check in the worklog smoke notes.
"""

from fastapi.testclient import TestClient

from app.adapters.base import AdapterError, BasePlatformAdapter, FakeAdapter
from app.main import app
from app.services.cache import SearchCache
from app.services.search import SearchService

client = TestClient(app)


class _CountingAdapter(BasePlatformAdapter):
    platform = "counting"

    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str) -> list[dict]:
        self.calls += 1
        return [
            {
                "id": "c-1",
                "platform": self.platform,
                "platform_stream_id": "c-1",
                "title": f"Result for {query}",
                "live_status": "live",
            }
        ]


class _FailingAdapter(BasePlatformAdapter):
    platform = "failing"

    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: str) -> list[dict]:
        self.calls += 1
        raise AdapterError("boom")


def _service(adapter, ttl: int = 60) -> SearchService:
    return SearchService(adapters=[adapter], cache=SearchCache(ttl_seconds=ttl))


def test_repeated_search_hits_cache():
    adapter = _CountingAdapter()
    service = _service(adapter)
    first = service.search("wildfire")
    second = service.search("wildfire")
    assert adapter.calls == 1
    assert second == first
    assert (service.stats.hits, service.stats.misses) == (1, 1)
    assert service.stats.adapter_calls == 1


def test_raw_variants_share_entry_but_synonyms_do_not():
    # Case/punctuation/whitespace share an entry. Synonym variants stay
    # separate on purpose: platforms match on raw wording, so "WILDFIRES"
    # may legitimately return different records than "wildfire".
    adapter = _CountingAdapter()
    service = _service(adapter)
    service.search("Wildfire!!")
    service.search("wildfire")
    assert adapter.calls == 1
    service.search("WILDFIRES")
    assert adapter.calls == 2


def test_different_queries_miss():
    adapter = _CountingAdapter()
    service = _service(adapter)
    service.search("wildfire")
    service.search("storm")
    assert adapter.calls == 2
    assert (service.stats.hits, service.stats.misses) == (0, 2)


def test_zero_ttl_never_hits():
    adapter = _CountingAdapter()
    service = _service(adapter, ttl=0)
    service.search("wildfire")
    service.search("wildfire")
    assert adapter.calls == 2


def test_failures_are_not_cached():
    adapter = _FailingAdapter()
    service = _service(adapter)
    for _ in range(2):
        try:
            service.search("wildfire")
        except AdapterError:
            pass
    assert adapter.calls == 2
    assert service.stats.adapter_errors == 2
    assert service.stats.hits == 0


def test_cache_key_mixes_platforms_and_normalizes():
    assert SearchCache.key("  WILDFIRE!! ", ("fake",)) == SearchCache.key(
        "wildfire", ("fake",)
    )
    assert SearchCache.key("wildfire", ("a",)) != SearchCache.key(
        "wildfire", ("b",)
    )


def test_expired_entries_purged_on_write():
    cache = SearchCache(ttl_seconds=0)
    service = SearchService(adapters=[FakeAdapter()], cache=cache)
    service.search("one")
    service.search("two")
    assert cache.size == 1  # first entry expired and purged by the second put


def test_stats_endpoint_shape():
    body = client.get("/api/stats").json()
    assert set(body) == {
        "cache_hits",
        "cache_misses",
        "adapter_calls",
        "adapter_errors",
        "cache_size",
        "index_records",
        "index_live",
    }
    assert all(isinstance(v, int) for v in body.values())
