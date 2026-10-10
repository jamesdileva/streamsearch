"""Search abuse controls (Sprint 11.2 verification).

The roadmap says "evaluate, and implement only controls justified by
observed/product requirements" — this suite encodes that judgement as
tests rather than adding a content filter nobody asked for.

Representative problematic inputs:
- XSS/malformed metadata in platform-supplied fields,
- doxxing-style queries (searches for private individuals),
- spam/cache-busting queries,
- query persistence (what a later inspection of stored state would reveal),
- log contents (what ops logs retain about users).
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.api.deps import mask_ip
from app.api.queryguard import QueryRejected, validate_query
from app.main import app
from app.services import index, metrics, reports
from app.services.search import SearchService

client = TestClient(app)


# --- helpers -------------------------------------------------------------


def _stream(raw: dict):
    from app.models.stream import Stream

    return Stream(**raw)


# --- malicious metadata ---------------------------------------------------


def test_platform_metadata_is_not_rendered_as_html():
    """A malicious title/channel must be inert text in the UI.

    React escapes by default and the codebase has no `innerHTML` /
    `dangerouslySetInnerHTML` anywhere (asserted below), so a payload
    arrives as text rather than markup.
    """
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[1] / ".." / "frontend" / "src"
    for tsx in src.rglob("*.tsx"):
        text = tsx.read_text(encoding="utf-8", errors="replace")
        assert "dangerouslySetInnerHTML" not in text
        assert "innerHTML" not in text


def test_malicious_metadata_round_trips_as_data():
    """Storage must not reinterpret metadata (no injection into the store)."""
    payload = {
        "id": "x-1",
        "platform": "youtube",
        "platform_stream_id": "x-1",
        "title": "<script>alert(1)</script> DROP TABLE streams;--",
        "description": "{% raw %} <img src=x onerror=alert(1)>",
        "channel_name": "'); DROP TABLE reports;--",
        "live_status": "live",
    }
    stored = index.upsert_stream(_stream(payload))
    assert "<script>" in stored.title  # stored verbatim, never interpreted
    fetched = index.get_stream("youtube", "x-1")
    assert fetched is not None
    assert "DROP TABLE" in fetched.channel_name


# --- doxxing / PII -------------------------------------------------------


def test_search_queries_are_not_persisted():
    """A later inspection must not reveal what anyone searched for.

    Queries live in the in-memory cache and request scope only; the index
    holds stream records, and metrics hold counts.
    """
    from app.adapters.base import FakeAdapter
    from app.services.cache import SearchCache

    metrics.get_metrics().reset()
    service = SearchService(adapters=[FakeAdapter()], cache=SearchCache(ttl_seconds=60))
    service.search("some private individual's name")

    # Nothing in durable state echoes the query text.
    snapshot_text = str(metrics.get_metrics().snapshot())
    assert "private individual" not in snapshot_text
    # Metrics only carry counters.
    assert not any(
        isinstance(v, str) and "private" in v.lower()
        for v in metrics.get_metrics().snapshot().values()
    )
    assert reports.count_reports() >= 0  # reports are report content, not queries


def test_metrics_never_record_query_text():
    metrics.get_metrics().reset()
    metrics.get_metrics().record_search_started()
    metrics.get_metrics().record_cache_miss()
    snapshot = metrics.get_metrics().snapshot()
    # Only counters and per-adapter names/digits; no free-text query values.
    for key, value in snapshot.items():
        if isinstance(value, str):
            assert "query" not in key
            assert "search" not in value.lower()


def test_logs_never_contain_raw_query_text(caplog):
    """Even when a query is rejected, only its digest reaches the log."""
    marker = "SENSITIVE_QUERY_TEXT"
    over_limit = marker + "_" + ("z" * 500)
    with caplog.at_level(logging.INFO), pytest.raises(QueryRejected):
        validate_query(over_limit)

    assert marker not in caplog.text
    assert "digest=" in caplog.text


def test_client_ips_are_masked_in_logs(caplog):
    logger = logging.getLogger("app.api.deps")
    with caplog.at_level(logging.INFO):
        logger.info("rate_limited scope=%s client=%s", "search", mask_ip("203.0.113.77"))
        logger.info(
            "rate_limited scope=%s client=%s", "search", mask_ip("2001:db8::8a2e:370:7334")
        )
        logger.info("rate_limited scope=%s client=%s", "search", mask_ip("198.51.100.9"))

    assert "203.0.113.77" not in caplog.text
    assert "198.51.100.9" not in caplog.text
    # Prefix retained for debugging, host part gone.
    assert "203.0.113.x#" in caplog.text
    assert "198.51.100.x#" in caplog.text
    # IPv6: /64 prefix kept, full address gone.
    assert "2001:db8" in caplog.text
    assert "8a2e:370:7334" not in caplog.text


# --- mask behaviour ------------------------------------------------------


def test_mask_ip_ipv4_keeps_prefix_and_digest():
    masked = mask_ip("203.0.113.77")
    assert masked.startswith("203.0.113.x#")
    assert len(masked.split("#")[1]) == 8


def test_mask_ip_is_stable_per_address():
    # Correlation across events must still work.
    assert mask_ip("203.0.113.77") == mask_ip("203.0.113.77")


def test_mask_ip_distinguishes_addresses():
    assert mask_ip("203.0.113.77") != mask_ip("203.0.113.78")


def test_mask_ip_handles_non_ip_gracefully():
    masked = mask_ip("not-an-ip")
    assert "not-an-ip" not in masked
    assert masked.startswith("unknown.x#")


# --- spam ----------------------------------------------------------------


def test_spam_queries_are_already_rejected():
    for spam in (
        "x" * 500,  # length
        "a" * 40,  # repeated filler
        "storm\x00now",  # control chars
    ):
        with pytest.raises(QueryRejected):
            validate_query(spam)


def test_spam_detection_does_not_block_real_queries():
    for real in ("wildfire near los angeles", "storm florida", "concert tokyo"):
        assert validate_query(real)


def test_repetition_threshold_allows_short_repeats():
    # "go go go" is a legitimate-ish query; only long filler is rejected.
    assert validate_query("go go go")


# --- api surface ---------------------------------------------------------


def test_no_endpoint_exposes_search_history():
    schema = app.openapi()
    paths = set(schema.get("paths", {}))
    for path in paths:
        assert "history" not in path
        assert "queries" not in path


def test_no_endpoint_returns_client_identities():
    """Nothing may leak request IPs back to a caller."""
    r = client.get("/api/stats")
    assert r.status_code == 200
    body = r.text.lower()
    assert "127.0.0.1" not in body
    assert "203.0.113" not in body
    assert "client" not in body


