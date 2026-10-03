"""Health route (moved out of main in Sprint 0.2)."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
