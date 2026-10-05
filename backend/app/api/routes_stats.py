"""Ops counters: GET /api/stats (Sprint 4.1 seed for 10.3 observability)."""

from fastapi import APIRouter

from app.services.index import index_counts
from app.services.search import get_search_service

router = APIRouter()


@router.get("/stats")
def stats() -> dict[str, int]:
    service = get_search_service()
    total, live = index_counts()
    return {
        **service.stats.snapshot(),
        "cache_size": service.cache.size,
        "index_records": total,
        "index_live": live,
    }
