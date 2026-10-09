"""In-memory rate limiting (Sprint 10.2).

Sliding-window counter per (scope, client). In-memory by design: the PoC runs
a single uvicorn process, and Redis stays unjustified until horizontal scaling
actually happens (see AGENTS.md §1). The consequence is honest — if we ever run
more than one worker behind a load balancer, each process enforces its own
window and the effective limit multiplies. That trade is recorded in the
worklog rather than discovered later.

Thread-safe: FastAPI runs sync endpoints in a threadpool, so hits can race.
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    limit: int
    window_seconds: float


class RateLimiter:
    def __init__(self, rules: dict[str, Rule] | None = None) -> None:
        self._rules: dict[str, Rule] = rules or {}
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def add_rule(self, scope: str, rule: Rule) -> None:
        with self._lock:
            self._rules[scope] = rule

    def _prune(self, key: str, rule: Rule, now: float) -> None:
        hits = self._hits[key]
        cutoff = now - rule.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()

    def check(self, scope: str, client: str) -> tuple[bool, int]:
        """Record a hit. Returns (allowed, remaining_after_this_hit).

        Unknown scopes are allowed (fail-open) so a missing rule never takes
        the service down; rules are opt-in per endpoint.
        """
        rule = self._rules.get(scope)
        if rule is None:
            return True, -1
        key = f"{scope}::{client}"
        now = time.monotonic()
        with self._lock:
            self._prune(key, rule, now)
            hits = self._hits[key]
            if len(hits) >= rule.limit:
                return False, 0
            hits.append(now)
            return True, rule.limit - len(hits)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
