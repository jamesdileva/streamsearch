"""Search: GET /api/search?q={query}."""

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.base import AdapterError
from app.models.stream import SearchResponse
from app.services.search import SearchService, get_search_service

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = "",
    service: SearchService = Depends(get_search_service),  # noqa: B008 - FastAPI idiom
) -> SearchResponse:
    if not q.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    try:
        return service.search(q)
    except AdapterError as exc:
        # A broken platform must not leak internals — 502 envelope.
        # Per-platform status + partial results land in Sprint 10.1.
        raise HTTPException(
            status_code=502, detail="live search temporarily unavailable"
        ) from exc
