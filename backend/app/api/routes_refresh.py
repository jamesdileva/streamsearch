"""Manual refresh trigger: POST /api/refresh (Sprint 4.3).

Same bounded pass the background loop runs. Authenticated in 10.2 by
**nothing** — rate-limited only, and deliberately so: the endpoint is
cheap-ish but quota-bearing, so it is limited to RATE_LIMIT_REFRESH per
window. Real auth is still owed before this is exposed publicly; the
worklog records that gap.
"""

from fastapi import APIRouter, Depends

from app.api.deps import rate_limit
from app.config import settings
from app.services.refresh import RefreshReport, run_refresh_once

router = APIRouter()


@router.post("/refresh", response_model=RefreshReport)
def trigger_refresh(
    _limited: None = Depends(rate_limit("refresh")),
) -> RefreshReport:
    return run_refresh_once(
        batch_size=settings.refresh_batch_size,
        prune_days=settings.refresh_prune_days,
    )
