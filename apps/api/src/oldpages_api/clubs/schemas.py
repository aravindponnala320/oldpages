from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

from oldpages_api.listings.schemas import ListingResponse

ClubVisibility = Literal["public", "private"]
BookClubStatus = Literal["active", "archived", "suspended"]
ClubBookStatus = Literal["current", "next", "past"]
BookNominationStatus = Literal["active", "selected", "withdrawn"]
MilestonePositionType = Literal["chapter", "page", "percent", "whole_book"]
BuddyReadStatus = Literal["active", "completed", "cancelled"]
ReadalongStatus = Literal["scheduled", "active", "completed", "cancelled"]
EventType = Literal[
    "book_club_meeting",
    "book_exchange",
    "used_book_fair",
    "donation_drive",
    "author_meetup",
    "signing",
    "reading_session",
    "silent_reading",
    "childrens_story_session",
    "library_event",
    "college_textbook_sale",
    "writing_workshop",
    "poetry_reading",
    "online_discussion",
    "author_interview",
]
EventStatus = Literal["scheduled", "cancelled", "completed"]
EventRSVPStatus = Literal["going", "cancelled", "waitlisted"]
EventWaitlistStatus = Literal["waiting", "promoted", "cancelled"]


class ClubUserSummary(BaseModel):
    id: str


class ClubBookSummary(BaseModel):
    id: str
    title: str


class BookClubCreateRequest(BaseModel):
    community_id: str | None = Field(default=None, max_length=26)
    description: str | None = Field(default=None, max_length=8000)
    name: str = Field(min_length=1, max_length=160)
    settings: dict[str, Any] = Field(default_factory=dict)
    slug: str | None = Field(default=None, max_length=180)
    timezone: str = Field(default="UTC", max_length=80)
    visibility: ClubVisibility = "public"

    @field_validator("community_id", "description", "name", "slug", "timezone")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        validate_timezone_name(value)
        return value


class BookClubResponse(BaseModel):
    community_id: str | None = None
    current_book: ClubBookSummary | None = None
    description: str | None = None
    id: str
    member_context: str | None = None
    name: str
    next_book: ClubBookSummary | None = None
    owner: ClubUserSummary
    slug: str
    status: BookClubStatus
    timezone: str
    visibility: ClubVisibility


class BookClubListResponse(BaseModel):
    items: list[BookClubResponse]
    next_cursor: str | None = None


class ClubBookCreateRequest(BaseModel):
    book_id: str = Field(min_length=1, max_length=26)
    discussion_guide: str | None = Field(default=None, max_length=8000)
    end_date: date | None = None
    start_date: date | None = None
    status: ClubBookStatus = "next"

    @model_validator(mode="after")
    def validate_dates(self) -> ClubBookCreateRequest:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class ClubBookResponse(BaseModel):
    available_listings: list[ListingResponse]
    book: ClubBookSummary
    discussion_guide: str | None = None
    end_date: date | None = None
    id: str
    selected_at: datetime | None = None
    sequence: int
    start_date: date | None = None
    status: ClubBookStatus


class ClubBookListResponse(BaseModel):
    items: list[ClubBookResponse]


class BookNominationCreateRequest(BaseModel):
    book_id: str = Field(min_length=1, max_length=26)
    cycle_key: str = Field(default="default", min_length=1, max_length=80)
    note: str | None = Field(default=None, max_length=4000)

    @field_validator("cycle_key", "note")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class BookNominationResponse(BaseModel):
    book: ClubBookSummary
    cycle_key: str
    id: str
    note: str | None = None
    nominator: ClubUserSummary
    status: BookNominationStatus
    vote_count: int


class BookVoteRequest(BaseModel):
    cycle_key: str = Field(default="default", min_length=1, max_length=80)
    nomination_id: str = Field(min_length=1, max_length=26)
    rank: int = Field(ge=1, le=100)


class BookVoteResponse(BaseModel):
    cycle_key: str
    id: str
    nomination_id: str
    rank: int
    voter: ClubUserSummary


class SelectClubBookRequest(BaseModel):
    cycle_key: str = Field(default="default", min_length=1, max_length=80)
    end_date: date | None = None
    start_date: date | None = None
    status: ClubBookStatus = "next"


class ReadingMilestoneCreateRequest(BaseModel):
    discussion_prompt: str | None = Field(default=None, max_length=8000)
    ends_at: datetime | None = None
    position_type: MilestonePositionType
    position_value: int = Field(ge=0)
    starts_at: datetime | None = None
    title: str = Field(min_length=1, max_length=180)

    @field_validator("ends_at", "starts_at")
    @classmethod
    def validate_aware_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            require_timezone_aware(value)
        return value


class ReadingMilestoneResponse(BaseModel):
    discussion_prompt: str | None = None
    ends_at: datetime | None = None
    id: str
    position_type: MilestonePositionType
    position_value: int
    spoiler_locked: bool
    starts_at: datetime | None = None
    title: str


class ReadingMilestoneListResponse(BaseModel):
    items: list[ReadingMilestoneResponse]


class BuddyReadCreateRequest(BaseModel):
    book_id: str = Field(min_length=1, max_length=26)
    deadline_at: datetime | None = None
    max_participants: int = Field(default=4, ge=2, le=20)
    title: str = Field(min_length=1, max_length=180)
    visibility: ClubVisibility = "private"

    @field_validator("deadline_at")
    @classmethod
    def validate_deadline(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            require_timezone_aware(value)
        return value


class BuddyReadProgressRequest(BaseModel):
    position_type: MilestonePositionType = "page"
    position_value: int = Field(ge=0)


class BuddyReadResponse(BaseModel):
    book: ClubBookSummary
    deadline_at: datetime | None = None
    id: str
    max_participants: int
    participant_user_ids: list[str]
    progress: dict[str, Any]
    status: BuddyReadStatus
    title: str
    visibility: ClubVisibility


class ReadalongCreateRequest(BaseModel):
    book_id: str = Field(min_length=1, max_length=26)
    chapter_schedule: list[dict[str, Any]] = Field(default_factory=list, max_length=200)
    community_id: str | None = Field(default=None, max_length=26)
    description: str | None = Field(default=None, max_length=8000)
    ends_at: datetime | None = None
    starts_at: datetime | None = None
    timezone: str = Field(default="UTC", max_length=80)
    title: str = Field(min_length=1, max_length=180)
    visibility: ClubVisibility = "public"

    @field_validator("ends_at", "starts_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            require_timezone_aware(value)
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        validate_timezone_name(value)
        return value


class ReadalongResponse(BaseModel):
    book: ClubBookSummary
    chapter_schedule: list[dict[str, Any]]
    community_id: str | None = None
    description: str | None = None
    ends_at: datetime | None = None
    id: str
    host: ClubUserSummary
    starts_at: datetime | None = None
    status: ReadalongStatus
    timezone: str
    title: str
    visibility: ClubVisibility


class EventCreateRequest(BaseModel):
    address: str | None = Field(default=None, max_length=4000)
    capacity: int | None = Field(default=None, ge=1, le=100_000)
    club_id: str | None = Field(default=None, max_length=26)
    community_id: str | None = Field(default=None, max_length=26)
    description: str | None = Field(default=None, max_length=8000)
    ends_at: datetime
    event_type: EventType
    location_name: str | None = Field(default=None, max_length=180)
    metadata: dict[str, Any] = Field(default_factory=dict)
    online_url: str | None = Field(default=None, max_length=1000)
    starts_at: datetime
    timezone: str = Field(max_length=80)
    title: str = Field(min_length=1, max_length=180)
    visibility: ClubVisibility = "public"

    @field_validator("ends_at", "starts_at")
    @classmethod
    def validate_datetime(cls, value: datetime) -> datetime:
        require_timezone_aware(value)
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        validate_timezone_name(value)
        return value

    @model_validator(mode="after")
    def validate_range(self) -> EventCreateRequest:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at.")
        return self


class EventUpdateRequest(BaseModel):
    capacity: int | None = Field(default=None, ge=1, le=100_000)
    description: str | None = Field(default=None, max_length=8000)
    ends_at: datetime | None = None
    location_name: str | None = Field(default=None, max_length=180)
    online_url: str | None = Field(default=None, max_length=1000)
    starts_at: datetime | None = None
    status: EventStatus | None = None
    timezone: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, max_length=180)

    @field_validator("ends_at", "starts_at")
    @classmethod
    def validate_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            require_timezone_aware(value)
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            validate_timezone_name(value)
        return value


class EventResponse(BaseModel):
    capacity: int | None = None
    checkin_code: str | None = None
    club_id: str | None = None
    community_id: str | None = None
    description: str | None = None
    ends_at: datetime
    event_type: EventType
    id: str
    location_name: str | None = None
    online_url: str | None = None
    organizer: ClubUserSummary
    rsvp_count: int
    starts_at: datetime
    status: EventStatus
    timezone: str
    title: str
    visibility: ClubVisibility
    waitlist_count: int


class EventListResponse(BaseModel):
    items: list[EventResponse]
    next_cursor: str | None = None


class EventRSVPRequest(BaseModel):
    guest_count: int = Field(default=0, ge=0, le=20)
    note: str | None = Field(default=None, max_length=500)


class EventRSVPResponse(BaseModel):
    event_id: str
    guest_count: int
    id: str
    status: EventRSVPStatus
    user: ClubUserSummary
    waitlist_position: int | None = None


class EventCheckinRequest(BaseModel):
    checkin_code: str = Field(min_length=1, max_length=32)
    user_id: str = Field(min_length=1, max_length=26)


class EventCheckinResponse(BaseModel):
    checked_in_at: datetime
    checked_in_by_user_id: str
    event_id: str
    id: str
    user_id: str


def require_timezone_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime must include a timezone offset.")


def validate_timezone_name(value: str) -> None:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("timezone must be a valid IANA timezone.") from exc
