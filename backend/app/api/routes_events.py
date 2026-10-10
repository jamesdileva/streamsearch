"""Event-detection prototype (Sprint 13.2): GET /api/events?q={query}.

Inspectable output for the roadmap's "move from stream search toward event
search" question. **Not** wired into search and **not** a product feature —
the roadmap frames 13.2 as an experiment, and the verdict lives in
`docs/event-detection.md`. Rate-limited as a search (it costs real quota).
"""

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.base import AdapterError
from app.api.deps import rate_limit, validated_query
from app.models.stream import SearchResponse
from app.search.events import EventProposal, detect_events
from app.services.search import SearchService, get_search_service

router = APIRouter()


@router.get("/events", response_model=list[EventProposal])
def events(
    clean_query: str = Depends(validated_query),
    service: SearchService = Depends(get_search_service),  # noqa: B008 - FastAPI idiom
    _limited: None = Depends(rate_limit("search")),
) -> list[EventProposal]:
    try:
        response: SearchResponse = service.search(clean_query)
    except AdapterError as exc:
        raise HTTPException(
            status_code=502, detail="live search temporarily unavailable"
        ) from exc
    return detect_events(response.results)
