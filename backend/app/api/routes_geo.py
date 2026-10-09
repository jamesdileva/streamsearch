"""Map prototype endpoint (Sprint 8.2): GET /api/geo?q={query}.

Returns markers, clusters, and — most importantly for this experiment —
measured location coverage. Read-only; no map UI is wired up yet, the
point is to measure whether the data could ever support one.

Runs the same cheap 0% coverage computation as Sprint 8.2; rate-limited as
a search from Sprint 10.2 onward.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.base import AdapterError
from app.api.deps import rate_limit, validated_query
from app.search.geo import MapPayload, build_map_payload
from app.services.search import SearchService, get_search_service

router = APIRouter()


@router.get("/geo", response_model=MapPayload)
def geo(
    clean_query: str = Depends(validated_query),
    service: SearchService = Depends(get_search_service),  # noqa: B008 - FastAPI idiom
    _limited: None = Depends(rate_limit("search")),
) -> MapPayload:
    try:
        response = service.search(clean_query)
    except AdapterError as exc:
        raise HTTPException(
            status_code=502, detail="live search temporarily unavailable"
        ) from exc
    return build_map_payload(response.results)
