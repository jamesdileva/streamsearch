"""StreamSearch API (Sprint 4.3: background refresh loop)."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.errors import register_error_handlers
from app.config import settings
from app.services.refresh import run_refresh_once

logger = logging.getLogger(__name__)


async def _refresh_loop() -> None:
    while True:
        await asyncio.sleep(settings.refresh_interval_seconds)
        try:
            report = run_refresh_once(
                batch_size=settings.refresh_batch_size,
                prune_days=settings.refresh_prune_days,
            )
            logger.info(
                "refresh pass: checked=%d refreshed=%d ended=%d pruned=%d errors=%d",
                report.checked,
                report.refreshed,
                report.ended,
                report.pruned,
                len(report.errors),
            )
        except Exception:
            logger.exception("refresh pass crashed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = None
    if settings.refresh_enabled:
        task = asyncio.create_task(_refresh_loop())
    yield
    if task is not None:
        task.cancel()


app = FastAPI(title="StreamSearch API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(api_router)
