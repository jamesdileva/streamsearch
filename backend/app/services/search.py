"""Search service placeholder (Sprint 0.2).

Fans out to adapters and maps raw dicts to the normalized Stream model.
No scoring yet — deterministic relevance lands in Sprint 3.1.
"""

from app.adapters.base import BasePlatformAdapter, FakeAdapter
from app.models.stream import SearchResponse, Stream


class SearchService:
    def __init__(self, adapters: list[BasePlatformAdapter] | None = None) -> None:
        self.adapters = adapters if adapters is not None else [FakeAdapter()]

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
