"""Search route skeleton: GET /api/search?q={query}."""

from fastapi import APIRouter, Depends, HTTPException

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
    return service.search(q)
