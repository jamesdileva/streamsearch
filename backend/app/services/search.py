"""Search service (Sprint 1.2).

Fans out to adapters and maps raw dicts to the normalized Stream model.
No scoring yet — deterministic relevance lands in Sprint 3.1.

Adapter selection is key-driven: the YouTube adapter is used only when
`YOUTUBE_API_KEY` is configured, otherwise the FakeAdapter skeleton stays
in place (real-query verification deferred until the key exists).
"""

from app.adapters.base import BasePlatformAdapter, FakeAdapter
from app.adapters.youtube import YouTubeAdapter
from app.config import settings
from app.models.stream import SearchResponse, Stream


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
    def __init__(self, adapters: list[BasePlatformAdapter] | None = None) -> None:
        self.adapters = adapters if adapters is not None else build_default_adapters()

    def search(self, query: str) -> SearchResponse:
        normalized = query.strip()
        results: list[Stream] = []
        for adapter in self.adapters:
            for raw in adapter.search(normalized):
                results.append(Stream(**raw))
        return SearchResponse(query=normalized, results=results, count=len(results))


_default_service = SearchService()


def get_search_service() -> SearchService:
    return _default_service
