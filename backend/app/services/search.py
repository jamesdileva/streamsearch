"""Search service (Sprint 3.1).

Fans out to adapters, maps raw dicts to the normalized Stream model,
stamps freshness, then ranks with deterministic scoring (app/search/scoring).
No semantic retrieval — that waits for the Sprint 7.1 failure dataset.

Adapter selection is key-driven: the YouTube adapter is used only when
`YOUTUBE_API_KEY` is configured, otherwise the FakeAdapter skeleton stays
in place (real-query verification deferred until the key exists).
"""

from app.adapters.base import BasePlatformAdapter, FakeAdapter
from app.adapters.youtube import YouTubeAdapter
from app.config import settings
from app.models.stream import SearchResponse, Stream
from app.search.scoring import Weights, rank_streams
from app.services.freshness import freshness_of


def build_default_adapters() -> list[BasePlatformAdapter]:
    if settings.youtube_api_key:
        return [
            YouTubeAdapter(
                api_key=settings.youtube_api_key,
                max_results=settings.youtube_max_results,
            )
        ]
    return [FakeAdapter()]


class SearchService:
    def __init__(
        self,
        adapters: list[BasePlatformAdapter] | None = None,
        weights: Weights | None = None,
    ) -> None:
        self.adapters = adapters if adapters is not None else build_default_adapters()
        self.weights = weights or Weights()

    def search(self, query: str) -> SearchResponse:
        normalized = query.strip()
        results: list[Stream] = []
        for adapter in self.adapters:
            for raw in adapter.search(normalized):
                stream = Stream(**raw)
                stream.freshness = freshness_of(
                    stream,
                    fresh_seconds=settings.freshness_fresh_seconds,
                    aging_seconds=settings.freshness_aging_seconds,
                )
                results.append(stream)
        ranked = rank_streams(results, normalized, self.weights)
        return SearchResponse(query=normalized, results=ranked, count=len(ranked))


_default_service = SearchService()


def get_search_service() -> SearchService:
    return _default_service
