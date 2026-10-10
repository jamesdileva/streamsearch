"""Shared request guards: client identity, rate limiting, query validation.

Client identity is the socket peer, NOT `X-Forwarded-For` — trusting a
client-supplied header would let anyone forge a bucket. Behind a real proxy,
set up a trusted-proxy middleware and adapt `client_key` deliberately.
"""

import hashlib
import logging
import secrets

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def require_refresh_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008 - FastAPI idiom
) -> None:
    """Guard the manual refresh trigger.

    Fail-closed in both directions:
    - no token configured (default) -> 503, endpoint disabled;
    - wrong/missing token -> 401.

    An open-by-default operational endpoint that spends quota was the
    exposure this closes (hardening sprint after 10.2).
    """
    configured = settings.refresh_token
    if not configured:
        raise HTTPException(
            status_code=503, detail="refresh endpoint is not configured"
        )
    presented = credentials.credentials if credentials else ""
    if not presented or not secrets.compare_digest(presented, configured):
        logger.info("refresh denied: bad credentials")
        raise HTTPException(
            status_code=401,
            detail="missing or invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

from app.api.queryguard import QueryRejected, validate_query
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


def mask_ip(ip: str) -> str:
    """Mask a client address for logging.

    The IP is the abuse-control key, but persisting raw addresses in
    indefinitely-retained logs is unnecessary PII collection (Sprint 11.2).
    Keep the network prefix (enough to see "one client is hammering us")
    plus a short digest (enough to correlate the same client across
    events), and drop the exact host part.
    """
    if ip.count(".") == 3:  # IPv4: keep /24
        prefix = ip.rsplit(".", 1)[0]
    elif ":" in ip:  # IPv6: keep the /64 prefix
        groups = ip.split(":")
        prefix = ":".join(groups[:4])
    else:
        prefix = "unknown"
    digest = hashlib.sha256(ip.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}.x#{digest}"


def rate_limit(scope: str):
    def guard(
        request: Request,
        client: str = Depends(client_key),
    ) -> None:
        from fastapi import HTTPException

        allowed, _remaining = limiter.check(scope, client)
        if not allowed:
            logger.info(
                "rate_limited scope=%s client=%s", scope, mask_ip(client)
            )
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
