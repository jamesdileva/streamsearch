"""Ops counters: GET /api/stats — the observability dashboard (Sprint 10.3).

A single JSON snapshot of everything the roadmap asks us to track: live
request/cache/latency counters, per-adapter health, index staleness, and
report volume. Intentionally read-only and cheap — this replaces "discovering
operational problems through user complaints".
"""

from fastapi import APIRouter

from app.services.metrics import observability_snapshot

router = APIRouter()


@router.get("/stats")
def stats() -> dict[str, object]:
    return observability_snapshot()
