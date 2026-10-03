"""Placeholder adapter interface (Sprint 0.1). Real YouTube adapter lands in 1.2."""

from abc import ABC, abstractmethod
from typing import Any


class BasePlatformAdapter(ABC):
    """Contract all platform adapters must implement.

    Search/business logic must depend on this, never on
    platform-specific response shapes.
    """

    platform: str = "base"

    @abstractmethod
    def search(self, query: str) -> list[dict[str, Any]]:
        """Return normalized stream dicts (see architecture §7)."""
        raise NotImplementedError


class FakeAdapter(BasePlatformAdapter):
    """Minimal stub to prove the normalization boundary (used in 0.2)."""

    platform = "fake"

    def search(self, query: str) -> list[dict[str, Any]]:
        return []
