"""API routing layer: all /api routes assemble here (Sprint 0.2)."""

from fastapi import APIRouter

from app.api.routes_geo import router as geo_router
from app.api.routes_health import router as health_router
from app.api.routes_refresh import router as refresh_router
from app.api.routes_reports import router as reports_router
from app.api.routes_search import router as search_router
from app.api.routes_stats import router as stats_router

api_router = APIRouter(prefix="/api")
api_router.include_router(geo_router)
api_router.include_router(health_router)
api_router.include_router(search_router)
api_router.include_router(reports_router)
api_router.include_router(stats_router)
api_router.include_router(refresh_router)
