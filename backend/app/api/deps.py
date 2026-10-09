"""Shared request guards: client identity, rate limiting, query validation.

Client identity is the socket peer, NOT `X-Forwarded-For` — trusting a
client-supplied header would let anyone forge a bucket. Behind a real proxy,
set up a trusted-proxy middleware and adapt `client_key` deliberately.
"""

import logging

from fastapi import Depends, Request

from app.api.queryguard import QueryRejected, validate_query
from app.config import settings
from app.services.ratelimit import RateLimiter, Rule

logger = logging.getLogger(__name__)


def build_limiter() -> RateLimiter:
    limiter = RateLimiter()
    limiter.add_rule(
        "search",
        Rule(settings.rate_limit_search, settings.rate_limit_search_window),
    )
    limiter.add_rule(
        "refresh",
        Rule(settings.rate_limit_refresh, settings.rate_limit_refresh_window),
    )
    return limiter


limiter = build_limiter()


def client_key(request: Request) -> str:
    """Rate-limit bucket identity: the peer address.

    `X-Forwarded-For` is intentionally ignored — it is client-controlled and
    would allow bucket spoofing. Adjust if/when a trusted proxy is added.
    """
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str):
    def guard(
        request: Request,
        client: str = Depends(client_key),
    ) -> None:
        from fastapi import HTTPException

        allowed, _remaining = limiter.check(scope, client)
        if not allowed:
            logger.info("rate_limited scope=%s client=%s", scope, client)
            raise HTTPException(
                status_code=429,
                detail="too many requests — slow down and retry shortly",
            )

    return guard


def validated_query(q: str = "") -> str:
    from fastapi import HTTPException

    try:
        return validate_query(q)
    except QueryRejected as exc:
        raise HTTPException(status_code=422, detail=exc.reason) from exc
