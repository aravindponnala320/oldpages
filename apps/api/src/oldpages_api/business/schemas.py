from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

BusinessType = Literal["individual", "shop", "publisher", "library", "institution"]
BusinessStatus = Literal["pending", "active", "suspended", "rejected"]
StaffRole = Literal["owner", "manager", "staff"]
StaffStatus = Literal["active", "suspended"]
ImportStatus = Literal["pending", "processing", "completed", "failed"]


class BusinessProfileCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    type: BusinessType = "individual"
    description: str | None = Field(default=None, max_length=4000)
    website: str | None = Field(default=None, max_length=500)

    @field_validator("name", "description", "website")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class BusinessProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    website: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    cover_url: str | None = Field(default=None, max_length=500)
    gstin: str | None = Field(default=None, max_length=20)

    @field_validator("name", "description", "website", "logo_url", "cover_url", "gstin")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class BusinessProfileResponse(BaseModel):
    id: str
    owner_user_id: str
    name: str
    slug: str
    type: BusinessType
    description: str | None = None
    logo_url: str | None = None
    cover_url: str | None = None
    website: str | None = None
    gstin: str | None = None
    status: BusinessStatus
    rejected_reason: str | None = None
    is_verified: bool
    verified_at: datetime | None = None
    listing_count: int
    created_at: datetime
    updated_at: datetime


class BusinessLocationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    address: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    pincode: str | None = Field(default=None, max_length=12)
    is_primary: bool = False

    @field_validator("name", "address", "city", "state", "pincode")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class BusinessLocationResponse(BaseModel):
    id: str
    business_profile_id: str
    name: str
    address: str
    city: str
    state: str
    country: str
    pincode: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class StaffInviteRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=26)
    role: StaffRole = "staff"
    permissions: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("permissions")
    @classmethod
    def normalize_permissions(cls, value: list[str]) -> list[str]:
        return sorted({permission.strip() for permission in value if permission.strip()})


class StaffAccountResponse(BaseModel):
    id: str
    user_id: str
    business_profile_id: str
    role: StaffRole
    permissions: list[str]
    status: StaffStatus
    invited_at: datetime | None = None
    accepted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApprovalActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class InventoryImportCreateRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=500)
    rows: list[dict[str, Any]] = Field(default_factory=list, max_length=10_000)
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("filename")
    @classmethod
    def strip_filename(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("filename is required")
        return stripped

    @field_validator("idempotency_key")
    @classmethod
    def strip_idempotency_key(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class InventoryImportResponse(BaseModel):
    id: str
    business_profile_id: str
    filename: str
    status: ImportStatus
    total_rows: int
    success_rows: int
    error_rows: int
    error_report_url: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
