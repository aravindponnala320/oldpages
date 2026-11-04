from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

ShelfType = Literal[
    "want_to_read",
    "currently_reading",
    "finished",
    "did_not_finish",
    "owned",
    "previously_owned",
    "available_for_exchange",
    "available_for_lending",
    "favorites",
    "academic_books",
    "rare_collection",
    "custom",
]
ShelfVisibility = Literal["public", "private"]
ReadingStatus = Literal["want_to_read", "currently_reading", "finished", "did_not_finish"]
ReadingNoteType = Literal["note", "highlight", "quote"]
ReadingNoteVisibility = Literal["private", "public"]
ReadingGoalType = Literal[
    "books_per_year",
    "pages_per_month",
    "minutes_per_day",
    "genre",
    "author",
    "language",
    "community_challenge",
    "institution_challenge",
]
ReadingGoalScope = Literal["personal", "community", "institution"]
ReadingGoalStatus = Literal["active", "completed", "cancelled"]
ReadingStatisticPeriod = Literal["month", "year", "all_time"]


class ReadingBookSummary(BaseModel):
    authors: list[str]
    genres: list[str]
    id: str
    page_count: int | None = None
    title: str


class ShelfCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    visibility: ShelfVisibility = "private"

    @field_validator("name", "slug")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class ShelfItemCreateRequest(BaseModel):
    book_id: str = Field(min_length=1, max_length=26)
    note: str | None = Field(default=None, max_length=4000)
    sort_order: int = Field(default=0, ge=0)


class ShelfItemResponse(BaseModel):
    added_at: datetime
    book: ReadingBookSummary
    id: str
    note: str | None = None
    sort_order: int


class ShelfResponse(BaseModel):
    id: str
    is_system: bool
    items: list[ShelfItemResponse]
    name: str
    shelf_type: ShelfType
    slug: str
    sort_order: int
    visibility: ShelfVisibility


class ShelfListResponse(BaseModel):
    items: list[ShelfResponse]


class ReadingProgressUpdateRequest(BaseModel):
    current_page: int | None = Field(default=None, ge=0)
    finished_on: date | None = None
    percent_complete: int | None = Field(default=None, ge=0, le=100)
    progressed_on: date | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    reading_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    reread_count: int | None = Field(default=None, ge=0)
    review_text: str | None = Field(default=None, max_length=8000)
    started_on: date | None = None
    status: ReadingStatus

    @model_validator(mode="after")
    def validate_dates(self) -> ReadingProgressUpdateRequest:
        if self.started_on and self.finished_on and self.finished_on < self.started_on:
            raise ValueError("finished_on must be on or after started_on.")
        return self


class ReadingProgressResponse(BaseModel):
    book: ReadingBookSummary
    current_page: int | None = None
    daily_minutes: dict[str, int]
    finished_on: date | None = None
    id: str
    last_progress_at: datetime | None = None
    percent_complete: int | None = None
    rating: int | None = None
    reread_count: int
    review_text: str | None = None
    started_on: date | None = None
    status: ReadingStatus
    total_reading_minutes: int


class ReadingProgressListResponse(BaseModel):
    items: list[ReadingProgressResponse]


class ReadingNoteCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=12000)
    book_id: str = Field(min_length=1, max_length=26)
    client_note_id: str | None = Field(default=None, max_length=120)
    note_type: ReadingNoteType = "note"
    page_number: int | None = Field(default=None, ge=0)
    percent_complete: int | None = Field(default=None, ge=0, le=100)
    visibility: ReadingNoteVisibility = "private"


class ReadingNoteResponse(BaseModel):
    body: str
    book: ReadingBookSummary
    created_at: datetime
    id: str
    note_type: ReadingNoteType
    page_number: int | None = None
    percent_complete: int | None = None
    visibility: ReadingNoteVisibility


class ReadingNoteListResponse(BaseModel):
    items: list[ReadingNoteResponse]


class ReadingGoalCreateRequest(BaseModel):
    community_id: str | None = Field(default=None, max_length=26)
    goal_type: ReadingGoalType
    period_end: date
    period_start: date
    scope: ReadingGoalScope = "personal"
    target_metadata: dict[str, Any] = Field(default_factory=dict)
    target_value: int = Field(gt=0)
    timezone: str = Field(default="UTC", max_length=80)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        validate_timezone_name(value)
        return value

    @model_validator(mode="after")
    def validate_goal(self) -> ReadingGoalCreateRequest:
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start.")
        if self.scope == "community" and not self.community_id:
            raise ValueError("community_id is required for community goals.")
        return self


class ReadingGoalResponse(BaseModel):
    community_id: str | None = None
    current_value: int
    goal_type: ReadingGoalType
    id: str
    period_end: date
    period_start: date
    scope: ReadingGoalScope
    status: ReadingGoalStatus
    target_metadata: dict[str, Any]
    target_value: int
    timezone: str


class ReadingGoalListResponse(BaseModel):
    items: list[ReadingGoalResponse]


class ReadingStatisticRecomputeRequest(BaseModel):
    period_start: date | None = None
    period_type: ReadingStatisticPeriod = "year"
    timezone: str = Field(default="UTC", max_length=80)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        validate_timezone_name(value)
        return value


class ReadingStatisticResponse(BaseModel):
    authors: dict[str, int]
    books_completed: int
    computed_at: datetime
    genres: dict[str, int]
    id: str
    minutes_read: int
    monthly_progress: dict[str, Any]
    pages_read: int
    period_end: date
    period_start: date
    period_type: ReadingStatisticPeriod
    reading_streak_days: int
    timezone: str
    year_summary: dict[str, Any]


class ReadingStatisticListResponse(BaseModel):
    items: list[ReadingStatisticResponse]


def validate_timezone_name(value: str) -> None:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("timezone must be a valid IANA timezone.") from exc
