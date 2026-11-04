from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

InstitutionType = Literal[
    "school",
    "college",
    "university",
    "library",
    "ngo",
    "coaching",
    "publisher",
    "bookstore",
    "other",
]
InstitutionStatus = Literal["pending", "active", "suspended", "rejected"]
MemberRole = Literal["admin", "staff", "student", "alumni", "member"]
MemberStatus = Literal["pending", "active", "suspended"]


class InstitutionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    type: InstitutionType
    description: str | None = Field(default=None, max_length=5000)
    website: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)

    @field_validator("name", "city", "state")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()

    @field_validator("description", "website")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class InstitutionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=5000)
    website: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    cover_url: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)

    @field_validator("name", "city", "state")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()

    @field_validator("description", "website", "logo_url", "cover_url")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class InstitutionResponse(BaseModel):
    id: str
    name: str
    slug: str
    type: InstitutionType
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    cover_url: str | None = None
    city: str | None = None
    state: str | None = None
    country: str
    is_verified: bool
    verified_at: datetime | None = None
    owner_user_id: str | None = None
    status: InstitutionStatus
    rejected_reason: str | None = None
    member_count: int
    created_at: datetime
    updated_at: datetime


class InstitutionMemberResponse(BaseModel):
    id: str
    institution_id: str
    user_id: str
    role: MemberRole
    status: MemberStatus
    joined_at: datetime | None = None
    email_verified: bool
    created_at: datetime


class JoinInstitutionRequest(BaseModel):
    role: MemberRole = "member"


class ApproveMemberRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=26)


class AddDomainRequest(BaseModel):
    domain: str = Field(min_length=1, max_length=253)

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str) -> str:
        return value.strip().lower()


class InstitutionDomainResponse(BaseModel):
    id: str
    institution_id: str
    domain: str
    is_verified: bool
    verified_at: datetime | None = None
    created_at: datetime


class ApprovalActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class InstitutionListResponse(BaseModel):
    items: list[InstitutionResponse]
    next_cursor: str | None = None
    total: int | None = None
