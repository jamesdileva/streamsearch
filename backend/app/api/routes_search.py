"""Search: GET /api/search?q={query}&platform=&sort=&has_location=&language=&min_viewers=."""

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.base import AdapterError
from app.api.deps import rate_limit, validated_query
from app.models.stream import SearchResponse
from app.search.scoring import SORTS
from app.services.search import SearchService, get_search_service

router = APIRouter()

_TRUTHY = {"1", "true", "yes"}
MAX_MIN_VIEWERS = 10_000_000


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = "",
    platform: str = "all",
    sort: str = "relevance",
    has_location: str = "",
    language: str = "",
    min_viewers: int = 0,
    service: SearchService = Depends(get_search_service),  # noqa: B008 - FastAPI idiom
    _limited: None = Depends(rate_limit("search")),
    clean_query: str = Depends(validated_query),
) -> SearchResponse:
    if sort not in SORTS:
        raise HTTPException(
            status_code=422, detail=f"unknown sort (expected one of {', '.join(SORTS)})"
        )
    if min_viewers < 0 or min_viewers > MAX_MIN_VIEWERS:
        raise HTTPException(
            status_code=422,
            detail=f"min_viewers must be between 0 and {MAX_MIN_VIEWERS}",
        )
    if not clean_query:
        # Unreachable: validated_query rejects empty queries first.
        raise HTTPException(status_code=422, detail="query must not be empty")
    try:
        response = service.search(
            clean_query,
            platform=platform,
            sort=sort,
            has_location=has_location.strip().lower() in _TRUTHY,
            language=language,
            min_viewers=min_viewers,
        )
    except AdapterError as exc:
        # A broken platform must not leak internals — 502 envelope.
        raise HTTPException(
            status_code=502, detail="live search temporarily unavailable"
        ) from exc
    # A partial outage still returns 200 with usable results (Sprint 10.1).
    # Only a total outage — no results *and* every platform errored — is a
    # 502, keeping failures visible instead of silently empty.
    if response.results or all(s.status == "ok" for s in response.platform_status):
        return response
    raise HTTPException(
        status_code=502, detail="live search temporarily unavailable"
    )
