"""Search service (Sprint 4.1).

Fans out to adapters, maps raw dicts to the normalized Stream model,
stamps freshness, ranks with deterministic scoring, and serves repeats
from a short-lived cache (app/services/cache.py) to protect platform quota.
No semantic retrieval — that waits for the Sprint 7.1 failure dataset.

Adapter selection is key-driven: the YouTube adapter is used only when
`YOUTUBE_API_KEY` is configured, otherwise the FakeAdapter skeleton stays
in place (real-query verification deferred until the key exists).
"""

from app.adapters.base import AdapterError, BasePlatformAdapter, FakeAdapter
from app.adapters.youtube import YouTubeAdapter
from app.config import settings
from app.models.stream import SearchResponse, Stream
from app.search.location import parse_location
from app.search.scoring import Weights, rank_streams
from app.services.cache import CacheStats, SearchCache
from app.services.freshness import freshness_of


def build_default_adapters() -> list[BasePlatformAdapter]:
    if settings.youtube_api_key:
        return [
            YouTubeAdapter(
                api_key=settings.youtube_api_key,
                max_results=settings.youtube_max_results,
                location_radius=settings.youtube_location_radius,
            )
        ]
    return [FakeAdapter()]


class SearchService:
    def __init__(
        self,
        adapters: list[BasePlatformAdapter] | None = None,
        weights: Weights | None = None,
        cache: SearchCache | None = None,
    ) -> None:
        self.adapters = adapters if adapters is not None else build_default_adapters()
        self.weights = weights or Weights()
        self.cache = cache or SearchCache(ttl_seconds=settings.cache_ttl_seconds)
        self.stats = CacheStats()

    def search(self, query: str) -> SearchResponse:
        normalized = query.strip()
        key = SearchCache.key(
            normalized, tuple(a.platform for a in self.adapters)
        )
        cached = self.cache.get(key)
        if cached is not None:
            self.stats.hits += 1
            return cached
        self.stats.misses += 1
        # Adapters receive the full query (platforms do their own matching);
        # ranking uses the parsed topic + place so location words don't
        # dilute text signals. Empty topic falls back to the full query.
        parsed = parse_location(normalized)
        text_query = parsed.topic or normalized
        results: list[Stream] = []
        for adapter in self.adapters:
            try:
                raw_records = adapter.search(normalized)
            except AdapterError:
                self.stats.adapter_errors += 1
                raise
            self.stats.adapter_calls += 1
            for raw in raw_records:
                stream = Stream(**raw)
                stream.freshness = freshness_of(
                    stream,
                    fresh_seconds=settings.freshness_fresh_seconds,
                    aging_seconds=settings.freshness_aging_seconds,
                )
                results.append(stream)
        ranked = rank_streams(results, text_query, self.weights, parsed.place)
        response = SearchResponse(query=normalized, results=ranked, count=len(ranked))
        self.cache.put(key, response)
        return response


_default_service = SearchService()


def get_search_service() -> SearchService:
    return _default_service
