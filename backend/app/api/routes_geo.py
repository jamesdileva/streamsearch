"""Map prototype endpoint (Sprint 8.2): GET /api/geo?q={query}.

Returns markers, clusters, and — most importantly for this experiment —
measured location coverage. Read-only; no map UI is wired up yet, the
point is to measure whether the data could ever support one.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.base import AdapterError
from app.search.geo import MapPayload, build_map_payload
from app.services.search import SearchResponse, SearchService, get_search_service

router = APIRouter()


@router.get("/geo", response_model=MapPayload)
def geo(
    q: str = "",
    service: SearchService = Depends(get_search_service),  # noqa: B008 - FastAPI idiom
) -> MapPayload:
    if not q.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    try:
        response: SearchResponse = service.search(q)
    except AdapterError as exc:
        raise HTTPException(
            status_code=502, detail="live search temporarily unavailable"
        ) from exc
    return build_map_payload(response.results)
