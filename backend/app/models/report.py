"""Report models (Sprint 2.3). Users feed corrections back into the index."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

ReportReason = Literal["broken_link", "no_longer_live", "wrong_topic", "other"]

MAX_DETAIL_CHARS = 500

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ReportCreate(BaseModel):
    stream_id: NonEmpty
    platform: str = ""
    reason: ReportReason
    detail: str = Field(default="", max_length=MAX_DETAIL_CHARS)


class Report(BaseModel):
    id: int
    stream_id: str
    platform: str
    reason: ReportReason
    detail: str
    created_at: datetime


class ReportList(BaseModel):
    reports: list[Report] = Field(default_factory=list)
    count: int = 0
