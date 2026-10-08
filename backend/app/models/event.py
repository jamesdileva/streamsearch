"""Event model (Sprint 6.1): one event → many broadcasts.

An Event groups normalized stream refs by (platform, platform_stream_id) —
the same identity the stream index uses. No automatic clustering here;
groups are created manually (6.2/6.3 experiment with detection). No API
endpoints yet — those come when the UI or clustering needs them.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from pydantic import BaseModel, Field, StringConstraints

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def new_event_id() -> str:
    return f"evt_{uuid4().hex[:12]}"


class EventStreamRef(BaseModel):
    platform: str
    platform_stream_id: str


class Event(BaseModel):
    event_id: str = Field(default_factory=new_event_id)
    topic: NonEmpty
    location: str | None = None
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    active_until: datetime | None = None
    related_streams: list[EventStreamRef] = Field(default_factory=list)

    def is_active(self, now: datetime | None = None) -> bool:
        at = now or datetime.now(timezone.utc)
        if self.active_until is None:
            return True
        end = self.active_until
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return end > at
