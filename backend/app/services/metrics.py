"""Operational metrics (Sprint 10.3): know whether the index is healthy.

Process-local counters, exposed via `GET /api/stats`. Deliberately NOT a
time-series store: the goal is "are things broken right now", not trend
analysis, and Prometheus/OTel would be unjustified until we have someone
watching dashboards.

Every metric here maps to an operational question:
  searches             — is anyone using it
  cache_hits/misses    — is the cache earning its keep
  adapter latency      — are platforms slow
  adapter errors       — are platforms broken
  streams_discovered   — is discovery finding *new* things
  stale/unverified     — is freshness decaying (4.3's job to fix)
  reports              — is the index quality being challenged
  api_requests/quota   — are we near platform limits
"""

import threading
import time
from dataclasses import dataclass, field

from app.models.report import ReportCreate
from app.services import index, reports


@dataclass
class AdapterMetrics:
    requests: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0
    last_error: str | None = None
    last_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        if not self.requests:
            return 0.0
        return round(self.total_latency_ms / self.requests, 2)


@dataclass
class MetricsRegistry:
    searches: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    streams_discovered: int = 0
    streams_indexed: int = 0
    api_requests: int = 0
    estimated_quota_units: int = 0
    started_at: float = field(default_factory=time.monotonic)
    adapters: dict[str, AdapterMetrics] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # -- recording ------------------------------------------------------

    def _adapter(self, name: str) -> AdapterMetrics:
        if name not in self.adapters:
            self.adapters[name] = AdapterMetrics()
        return self.adapters[name]

    def record_search_started(self) -> None:
        with self._lock:
            self.searches += 1

    def record_cache_hit(self) -> None:
        with self._lock:
            self.cache_hits += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self.cache_misses += 1

    def record_adapter_success(self, name: str, latency_ms: float) -> None:
        with self._lock:
            entry = self._adapter(name)
            entry.requests += 1
            entry.total_latency_ms += latency_ms
            entry.last_latency_ms = round(latency_ms, 2)
            self.api_requests += 1

    def record_adapter_error(self, name: str, message: str) -> None:
        with self._lock:
            entry = self._adapter(name)
            entry.errors += 1
            entry.last_error = message[:200]
            self.api_requests += 1

    def record_index_write(self, discovered: bool) -> None:
        with self._lock:
            self.streams_indexed += 1
            if discovered:
                self.streams_discovered += 1

    def add_quota_estimate(self, units: int) -> None:
        with self._lock:
            self.estimated_quota_units += units

    # -- snapshot -------------------------------------------------------

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            total_attempts = (
                sum(a.requests for a in self.adapters.values())
                + sum(a.errors for a in self.adapters.values())
            )
            total_errors = sum(a.errors for a in self.adapters.values())
            return {
                "uptime_seconds": round(time.monotonic() - self.started_at),
                "searches": self.searches,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": (
                    round(self.cache_hits / (self.cache_hits + self.cache_misses), 4)
                    if (self.cache_hits + self.cache_misses)
                    else 0.0
                ),
                "api_requests": self.api_requests,
                "estimated_quota_units": self.estimated_quota_units,
                # Denominator is every attempt (success + failure), so a
                # total outage reads 1.0 rather than a misleading 0.0.
                "adapter_requests": total_attempts,
                "adapter_errors": total_errors,
                "adapter_error_rate": (
                    round(total_errors / total_attempts, 4) if total_attempts else 0.0
                ),
                "streams_discovered": self.streams_discovered,
                "streams_indexed": self.streams_indexed,
                "adapters": {
                    name: {
                        "requests": a.requests,
                        "errors": a.errors,
                        "avg_latency_ms": a.avg_latency_ms,
                        "last_latency_ms": a.last_latency_ms,
                        "last_error": a.last_error,
                    }
                    for name, a in sorted(self.adapters.items())
                },
            }

    def reset(self) -> None:
        with self._lock:
            self.searches = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.streams_discovered = 0
            self.streams_indexed = 0
            self.api_requests = 0
            self.estimated_quota_units = 0
            self.started_at = time.monotonic()
            self.adapters.clear()


_registry = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    return _registry


def observability_snapshot() -> dict[str, object]:
    """Full dashboard payload: live counters + durable store health."""
    metrics = get_metrics().snapshot()
    totals = index.index_stats()
    try:
        report_count = reports.count_reports()
    except OSError:
        # Observability must never break the service it observes.
        report_count = -1
    return {
        "live": metrics,
        "index": totals,
        "reports": {"count": report_count},
    }


__all__ = [
    "AdapterMetrics",
    "MetricsRegistry",
    "ReportCreate",
    "get_metrics",
    "observability_snapshot",
]
