"""Manual refresh trigger: POST /api/refresh (Sprint 4.3).

Same bounded pass the background loop runs. No auth in the PoC — abuse
controls land in 10.2/11.2; do not expose this trigger publicly until then.
"""

from fastapi import APIRouter

from app.config import settings
from app.services.refresh import RefreshReport, run_refresh_once

router = APIRouter()


@router.post("/refresh", response_model=RefreshReport)
def trigger_refresh() -> RefreshReport:
    return run_refresh_once(
        batch_size=settings.refresh_batch_size,
        prune_days=settings.refresh_prune_days,
    )
