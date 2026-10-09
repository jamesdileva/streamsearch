"""Query validation / abuse heuristics (Sprint 10.2).

Deliberately minimal and structural rather than semantic: we reject inputs
that waste platform quota (cache-busting uniqueness), can't match anything
useful, or are malformed (control characters). We do NOT build a content
filter — that is not this system's job and Sprint 11.2 owns the real
abuse-policy questions.

Every rejection is logged with length + a stable digest, never the raw
query, so user input doesn't pile up in the logs.
"""

import hashlib
import logging
import re

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 200
MAX_REPEATED_CHARS = 20
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class QueryRejected(ValueError):
    """Carries a safe, user-facing reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _digest(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8", "replace")).hexdigest()[:12]


def validate_query(query: str) -> str:
    """Return the cleaned query, or raise QueryRejected with a safe reason.

    Cleaning is light (whitespace collapse) — semantic normalization lives in
    `app/search/normalize.py`.
    """
    cleaned = " ".join((query or "").split())
    if not cleaned:
        logger.info("query rejected: empty")
        raise QueryRejected("query must not be empty")

    if len(cleaned) > MAX_QUERY_LENGTH:
        logger.info(
            "query rejected: too_long len=%d digest=%s", len(cleaned), _digest(cleaned)
        )
        raise QueryRejected(
            f"query must be at most {MAX_QUERY_LENGTH} characters"
        )

    if CONTROL_CHARS.search(cleaned):
        logger.info("query rejected: control_chars digest=%s", _digest(cleaned))
        raise QueryRejected("query contains invalid characters")

    if re.search(rf"(.)\1{{{MAX_REPEATED_CHARS},}}", cleaned):
        logger.info("query rejected: repetition digest=%s", _digest(cleaned))
        raise QueryRejected("query looks like repeated filler")

    return cleaned
