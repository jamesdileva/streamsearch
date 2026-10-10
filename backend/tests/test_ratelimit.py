"""Rate limiting + abuse protection (Sprint 10.2 verification).

The roadmap asks for automated request burst tests. These burst the limiter
directly and through the API, and cover the query-side guards: length,
control characters, repeated filler — plus the privacy guarantee that raw
queries never reach the logs.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.api.queryguard import MAX_QUERY_LENGTH, QueryRejected, validate_query
from app.config import settings
from app.main import app
from app.services.ratelimit import RateLimiter, Rule

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_limiter():
    # The limiter is process-global, so other suites sharing the default
    # 60/min budget could be starved. Give every test a generous scope and a
    # clean state, then restore.
    deps.limiter.reset()
    deps.limiter.add_rule("search", Rule(limit=1000, window_seconds=60))
    deps.limiter.add_rule("refresh", Rule(limit=1000, window_seconds=60))
    yield
    deps.limiter.reset()


def test_burst_exceeds_limit_then_429_envelope():
    deps.limiter.add_rule("search", Rule(limit=3, window_seconds=60))
    codes = []
    for _ in range(4):
        r = client.get("/api/search", params={"q": "storm"})
        codes.append(r.status_code)
    assert codes == [200, 200, 200, 429]
    assert client.get("/api/search", params={"q": "storm"}).json() == {
        "error": {
            "code": 429,
            "message": "too many requests — slow down and retry shortly",
        }
    }


def test_limits_are_per_client_not_per_header():
    """X-Forwarded-For is ignored: buckets are the peer, not a client header."""
    deps.limiter.add_rule("search", Rule(limit=2, window_seconds=60))
    for _ in range(2):
        assert client.get("/api/search", params={"q": "storm"}).status_code == 200
    # Spoofing a different address must NOT buy a new bucket.
    spoofed = client.get(
        "/api/search",
        params={"q": "storm"},
        headers={"X-Forwarded-For": "203.0.113.9"},
    )
    assert spoofed.status_code == 429


def test_unknown_scope_fails_open():
    limiter = RateLimiter()
    allowed, remaining = limiter.check("no-such-scope", "1.2.3.4")
    assert allowed is True
    assert remaining == -1


def test_refresh_is_limited_tightly(monkeypatch):
    deps.limiter.reset()
    deps.limiter.add_rule("refresh", Rule(limit=2, window_seconds=300))
    monkeypatch.setattr(settings, "refresh_token", "t")
    codes = [
        client.post(
            "/api/refresh", headers={"Authorization": "Bearer t"}
        ).status_code
        for _ in range(3)
    ]
    assert codes == [200, 200, 429]


def test_health_is_not_rate_limited():
    deps.limiter.add_rule("search", Rule(limit=1, window_seconds=60))
    # Even an absurd search limit must not take down health checks.
    for _ in range(5):
        assert client.get("/api/health").status_code == 200


def test_over_limit_query_is_rejected():
    with pytest.raises(QueryRejected):
        validate_query("a" * (MAX_QUERY_LENGTH + 1))


def test_control_characters_are_rejected():
    with pytest.raises(QueryRejected):
        validate_query("storm\x00now")


def test_repeated_filler_is_rejected():
    with pytest.raises(QueryRejected):
        validate_query("a" * 40)


def test_normal_queries_pass_validation():
    assert validate_query("  wildfire   near LA ") == "wildfire near LA"
    assert validate_query(" storm in Florida ") == "storm in Florida"


def test_api_rejects_over_limit_query():
    r = client.get("/api/search", params={"q": "x" * 500})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == 422
    assert "at most" in r.json()["error"]["message"]


def test_api_rejects_control_chars():
    r = client.get("/api/search", params={"q": "bad\x01query"})
    assert r.status_code == 422


def test_raw_query_never_reaches_logs(caplog):
    """Privacy: rejections log length + digest, never the user's input."""
    secret_query = "PRIVATE_USER_INPUT_" + "z" * 50
    with caplog.at_level(logging.INFO):
        with pytest.raises(QueryRejected):
            validate_query(secret_query)
        with pytest.raises(QueryRejected):
            validate_query("clean\x02control")

    # The raw query body never appears; reason labels and the digest are the
    # intended log content.
    assert secret_query not in caplog.text
    assert "PRIVATE" not in caplog.text
    assert "digest=" in caplog.text
