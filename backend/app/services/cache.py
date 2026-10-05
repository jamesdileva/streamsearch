"""Short-lived in-memory result cache + counters (Sprint 4.1).

Keyed by normalized query (+ adapter set, so a key arriving mid-process
can't serve skeleton records as YouTube ones). TTL-bounded; expired entries
are purged on access so the dict can't grow without bound. Only successful
responses are cached — failures must stay visible and retryable.

Freshness labels inside cached responses age with the entry (bounded by
the short TTL). The persistent index (4.2) and revalidation (4.3) own
long-term freshness; this cache only protects platform quota.
"""

import threading
import time
from dataclasses import dataclass

from app.models.stream import SearchResponse
from app.search.normalize import normalized_text


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    adapter_calls: int = 0
    adapter_errors: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "adapter_calls": self.adapter_calls,
            "adapter_errors": self.adapter_errors,
        }


class SearchCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = max(0, ttl_seconds)
        self._entries: dict[str, tuple[SearchResponse, float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def key(query: str, platforms: tuple[str, ...]) -> str:
        return f"{'|'.join(platforms)}::{normalized_text(query)}"

    def _purge_expired(self, now: float) -> None:
        expired = [k for k, (_, exp) in self._entries.items() if exp <= now]
        for k in expired:
            del self._entries[k]

    def get(self, key: str) -> SearchResponse | None:
        now = time.monotonic()
        with self._lock:
            found = self._entries.get(key)
            if found is None:
                return None
            response, expires_at = found
            if expires_at <= now:
                del self._entries[key]
                return None
            return response

    def put(self, key: str, response: SearchResponse) -> None:
        now = time.monotonic()
        with self._lock:
            self._purge_expired(now)
            self._entries[key] = (response, now + self.ttl_seconds)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)
