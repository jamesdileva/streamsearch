"""Manual refresh trigger: POST /api/refresh (Sprint 4.3, hardened later).

Same bounded pass the background loop runs. The endpoint spends platform
quota, so it requires a bearer token configured via `REFRESH_TOKEN`
(absent by default, which disables it — fail closed). The background loop
is unaffected and needs no credentials.
"""

from fastapi import APIRouter, Depends

from app.api.deps import rate_limit, require_refresh_token
from app.config import settings
from app.services.refresh import RefreshReport, run_refresh_once

router = APIRouter()


@router.post("/refresh", response_model=RefreshReport)
def trigger_refresh(
    _auth: None = Depends(require_refresh_token),
    _limited: None = Depends(rate_limit("refresh")),
) -> RefreshReport:
    return run_refresh_once(
        batch_size=settings.refresh_batch_size,
        prune_days=settings.refresh_prune_days,
    )
