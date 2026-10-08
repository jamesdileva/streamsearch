"""Search service (Sprint 4.1).

Fans out to adapters, maps raw dicts to the normalized Stream model,
stamps freshness, ranks with deterministic scoring, and serves repeats
from a short-lived cache (app/services/cache.py) to protect platform quota.
No semantic retrieval — that waits for the Sprint 7.1 failure dataset.

Adapter selection is key-driven: YouTube and Twitch adapters are used only
when their credentials are configured (independently combinable); otherwise
the fake platforms stay in place. Fakes are never mixed with real adapters.
"""

import logging

from app.adapters.base import AdapterError, BasePlatformAdapter, FakeAdapter
from app.adapters.fake_twitch import FakeTwitchAdapter
from app.adapters.twitch import TwitchAdapter
from app.adapters.youtube import YouTubeAdapter
from app.config import settings
from app.models.stream import SearchResponse, Stream
from app.search.dedup import dedupe_streams
from app.search.location import parse_location
from app.search.scoring import Weights, rank_streams, sort_streams
from app.services.cache import CacheStats, SearchCache
from app.services.freshness import freshness_of
from app.services.index import upsert_stream

logger = logging.getLogger(__name__)


def build_default_adapters() -> list[BasePlatformAdapter]:
    adapters: list[BasePlatformAdapter] = []
    if settings.youtube_api_key:
        adapters.append(
            YouTubeAdapter(
                api_key=settings.youtube_api_key,
                max_results=settings.youtube_max_results,
                location_radius=settings.youtube_location_radius,
            )
        )
    if settings.twitch_client_id and settings.twitch_client_secret:
        adapters.append(
            TwitchAdapter(
                client_id=settings.twitch_client_id,
                client_secret=settings.twitch_client_secret,
                max_results=settings.twitch_max_results,
                max_categories=settings.twitch_max_categories,
                embed_parent=settings.twitch_embed_parent,
            )
        )
    if adapters:
        return adapters
    # No keys: two fake platforms, proving the mixed-platform chain
    # (Sprint 5.1). Never mixed with real adapters.
    return [FakeAdapter(), FakeTwitchAdapter()]


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

    def search(
        self,
        query: str,
        platform: str = "all",
        sort: str = "relevance",
        has_location: bool = False,
        language: str = "",
        min_viewers: int = 0,
    ) -> SearchResponse:
        normalized = query.strip()
        platform_filter = platform.strip().lower()
        language_filter = language.strip().lower()
        min_viewers = max(0, int(min_viewers))
        key = SearchCache.key(
            normalized,
            tuple(a.platform for a in self.adapters),
            platform_filter,
            sort,
            has_location,
            language_filter,
            min_viewers,
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
        if platform_filter and platform_filter != "all":
            wanted = {p.strip() for p in platform_filter.split(",") if p.strip()}
            results = [s for s in results if s.platform in wanted]
        if has_location:
            results = [
                s
                for s in results
                if s.location_text or (s.latitude is not None and s.longitude is not None)
            ]
        if language_filter:
            results = [s for s in results if s.language == language_filter]
        if min_viewers:
            # Records without viewer data can't satisfy a floor, so they're
            # excluded rather than silently passed through.
            results = [s for s in results if (s.viewer_count or 0) >= min_viewers]
        ranked = rank_streams(results, text_query, self.weights, parsed.place)
        # Collapse obvious duplicates for the response (best-ranked survives);
        # the index keeps every sighting the platforms reported.
        deduped, removed = dedupe_streams(ranked)
        ordered = sort_streams(deduped, sort)
        response = SearchResponse(
            query=normalized,
            results=ordered,
            count=len(ordered),
            duplicates_removed=removed,
        )
        self._store_in_index(ranked)
        self.cache.put(key, response)
        return response

    @staticmethod
    def _store_in_index(streams: list[Stream]) -> None:
        # The index must never break search: a failing store is logged and
        # skipped (operational visibility lands in Sprint 10.3).
        for stream in streams:
            try:
                upsert_stream(stream)
            except Exception:
                logger.warning("index upsert failed", exc_info=True)


_default_service = SearchService()


def get_search_service() -> SearchService:
    return _default_service
