from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from oldpages_api.listings.schemas import ListingResponse

CommunityVisibility = Literal["public", "private", "secret", "institution_verified"]
CommunityMembershipPolicy = Literal["open", "request", "approval", "institution_verified"]
CommunityType = Literal[
    "college",
    "university",
    "school",
    "area",
    "city",
    "apartment",
    "workplace",
    "language",
    "genre",
    "author",
    "series",
    "book",
    "exam",
    "course",
    "profession",
    "age_group",
    "reading_goal",
    "library",
    "bookstore",
    "publisher",
    "social_cause",
    "local",
    "general",
]
CommunityMemberStatus = Literal["pending", "active", "rejected", "banned", "muted"]
CommunityChannelType = Literal["general", "announcements", "marketplace", "questions", "resources"]
CommunityChannelVisibility = Literal["public", "members", "moderators"]
CommunityPostType = Literal[
    "text",
    "review",
    "photo",
    "video",
    "poll",
    "question",
    "recommendation",
    "quote",
    "reading_update",
    "listing",
    "exchange_request",
    "donation_request",
    "event",
    "challenge",
    "resource",
    "announcement",
]
CommunityPostStatus = Literal["published", "pending_review", "hidden", "deleted"]
PostReactionType = Literal["like", "love", "insightful", "upvote", "celebrate"]
CommunityReportTargetType = Literal["community", "post", "comment", "member"]
CommunityReportStatus = Literal["open", "resolved", "dismissed"]


class CommunityRuleInput(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    title: str = Field(min_length=1, max_length=160)

    @field_validator("body", "title")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class CommunityChannelInput(BaseModel):
    channel_type: CommunityChannelType = "general"
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    visibility: CommunityChannelVisibility = "members"

    @field_validator("name", "slug")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class CommunityCreateRequest(BaseModel):
    book_id: str | None = Field(default=None, max_length=26)
    channels: list[CommunityChannelInput] = Field(default_factory=list, max_length=12)
    city: str | None = Field(default=None, max_length=120)
    community_type: CommunityType = "general"
    country: str | None = Field(default=None, max_length=80)
    cover_image_url: str | None = Field(default=None, max_length=1000)
    description: str | None = Field(default=None, max_length=8000)
    genre: str | None = Field(default=None, max_length=120)
    institution: str | None = Field(default=None, max_length=180)
    language: str | None = Field(default=None, max_length=40)
    membership_policy: CommunityMembershipPolicy | None = None
    name: str = Field(min_length=1, max_length=120)
    rules: list[CommunityRuleInput] = Field(default_factory=list, max_length=20)
    settings: dict[str, Any] = Field(default_factory=dict)
    slug: str | None = Field(default=None, max_length=140)
    state: str | None = Field(default=None, max_length=120)
    visibility: CommunityVisibility = "public"

    @field_validator(
        "city",
        "country",
        "cover_image_url",
        "description",
        "genre",
        "institution",
        "language",
        "name",
        "slug",
        "state",
    )
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_scope(self) -> CommunityCreateRequest:
        if self.visibility == "institution_verified" and not self.institution:
            raise ValueError("institution is required for institution-verified communities.")
        return self


class CommunityJoinRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


class CommunityApproveMemberRequest(BaseModel):
    role: Literal["member", "moderator"] = "member"
    user_id: str = Field(min_length=1, max_length=26)


class CommunityPostCreateRequest(BaseModel):
    body: str | None = Field(default=None, max_length=8000)
    channel_id: str | None = Field(default=None, max_length=26)
    is_announcement: bool = False
    is_pinned: bool = False
    listing_id: str | None = Field(default=None, max_length=26)
    poll_options: list[str] = Field(default_factory=list, max_length=12)
    post_type: CommunityPostType = "text"
    title: str | None = Field(default=None, max_length=240)

    @field_validator("body", "channel_id", "listing_id", "title")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("poll_options")
    @classmethod
    def strip_poll_options(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_post(self) -> CommunityPostCreateRequest:
        if not self.title and not self.body and not self.poll_options and not self.listing_id:
            raise ValueError("A post requires a title, body, poll options, or listing.")
        if self.post_type == "poll" and len(self.poll_options) < 2:
            raise ValueError("Poll posts require at least two options.")
        if self.post_type == "listing" and not self.listing_id:
            raise ValueError("Listing posts require listing_id.")
        return self


class PostCommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    parent_comment_id: str | None = Field(default=None, max_length=26)

    @field_validator("body")
    @classmethod
    def strip_body(cls, value: str) -> str:
        return value.strip()


class PostReactionRequest(BaseModel):
    reaction_type: PostReactionType = "like"


class CommunityReportCreateRequest(BaseModel):
    details: str | None = Field(default=None, max_length=4000)
    reason: str = Field(min_length=1, max_length=80)
    target_id: str | None = Field(default=None, max_length=26)
    target_type: CommunityReportTargetType

    @field_validator("details", "reason", "target_id")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class CommunityUserSummary(BaseModel):
    id: str


class CommunityRoleResponse(BaseModel):
    id: str
    is_default: bool
    name: str
    permissions: list[str]


class CommunityMemberResponse(BaseModel):
    joined_at: datetime | None = None
    role: str
    status: CommunityMemberStatus
    user: CommunityUserSummary


class CommunityRuleResponse(BaseModel):
    body: str
    enabled: bool
    id: str
    sort_order: int
    title: str


class CommunityChannelResponse(BaseModel):
    channel_type: CommunityChannelType
    id: str
    name: str
    slug: str
    visibility: CommunityChannelVisibility


class CommunitySummaryResponse(BaseModel):
    book_id: str | None = None
    city: str | None = None
    community_type: CommunityType
    country: str | None = None
    description: str | None = None
    genre: str | None = None
    id: str
    institution: str | None = None
    member_count: int
    name: str
    slug: str
    state: str | None = None
    visibility: CommunityVisibility
    viewer_membership_status: CommunityMemberStatus | None = None


class CommunityResponse(CommunitySummaryResponse):
    channels: list[CommunityChannelResponse]
    membership_policy: CommunityMembershipPolicy
    owner: CommunityUserSummary
    rules: list[CommunityRuleResponse]


class CommunityListResponse(BaseModel):
    items: list[CommunitySummaryResponse]
    next_cursor: str | None = None


class CommunityPostResponse(BaseModel):
    author: CommunityUserSummary
    body: str | None = None
    channel_id: str | None = None
    comment_count: int
    community_id: str
    created_at: datetime
    id: str
    is_announcement: bool
    is_pinned: bool
    listing_id: str | None = None
    poll: dict[str, Any]
    post_type: CommunityPostType
    reaction_counts: dict[str, int]
    status: CommunityPostStatus
    title: str | None = None
    viewer_reaction: PostReactionType | None = None


class CommunityFeedResponse(BaseModel):
    items: list[CommunityPostResponse]
    next_cursor: str | None = None


class PostCommentResponse(BaseModel):
    author: CommunityUserSummary
    body: str
    created_at: datetime
    id: str
    parent_comment_id: str | None = None
    post_id: str
    status: str


class PostReactionResponse(BaseModel):
    id: str
    post_id: str
    reaction_type: PostReactionType
    user_id: str


class CommunityMarketplaceResponse(BaseModel):
    community_id: str
    items: list[ListingResponse]
    next_cursor: str | None = None


class CommunityReportResponse(BaseModel):
    community_id: str
    created_at: datetime
    id: str
    reason: str
    status: CommunityReportStatus
    target_id: str | None = None
    target_type: CommunityReportTargetType

    model_config = ConfigDict(extra="forbid")
