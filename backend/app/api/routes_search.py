"""Search: GET /api/search?q={query}&platform=&sort=&has_location=."""

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.base import AdapterError
from app.models.stream import SearchResponse
from app.search.scoring import SORTS
from app.services.search import SearchService, get_search_service

router = APIRouter()

_TRUTHY = {"1", "true", "yes"}


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = "",
    platform: str = "all",
    sort: str = "relevance",
    has_location: str = "",
    service: SearchService = Depends(get_search_service),  # noqa: B008 - FastAPI idiom
) -> SearchResponse:
    if not q.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    if sort not in SORTS:
        raise HTTPException(
            status_code=422, detail=f"unknown sort (expected one of {', '.join(SORTS)})"
        )
    try:
        return service.search(
            q,
            platform=platform,
            sort=sort,
            has_location=has_location.strip().lower() in _TRUTHY,
        )
    except AdapterError as exc:
        # A broken platform must not leak internals — 502 envelope.
        # Per-platform status + partial results land in Sprint 10.1.
        raise HTTPException(
            status_code=502, detail="live search temporarily unavailable"
        ) from exc
