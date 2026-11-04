from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CampaignStatus = Literal["draft", "active", "paused", "completed", "cancelled"]
PledgeStatus = Literal["pending", "accepted", "pickup_scheduled", "received", "cancelled"]


class DonationNeedInput(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    author: str | None = Field(default=None, max_length=500)
    book_id: str | None = Field(default=None, max_length=26)
    quantity_needed: int = Field(ge=1)

    @field_validator("title", "author")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class CampaignCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=10000)
    accepted_conditions: list[str] = Field(default_factory=list, max_length=20)
    quantity_target: int = Field(ge=1)
    pickup_address: str | None = Field(default=None, max_length=500)
    dropoff_address: str | None = Field(default=None, max_length=500)
    deadline_at: datetime | None = None
    is_public: bool = True
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    institution_id: str | None = Field(default=None, max_length=26)
    needs: list[DonationNeedInput] = Field(default_factory=list, max_length=50)

    @field_validator("title", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("pickup_address", "dropoff_address", "city", "state")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class CampaignUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    accepted_conditions: list[str] | None = None
    pickup_address: str | None = Field(default=None, max_length=500)
    dropoff_address: str | None = Field(default=None, max_length=500)
    deadline_at: datetime | None = None
    is_public: bool | None = None
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)


class DonationNeedResponse(BaseModel):
    id: str
    campaign_id: str
    book_id: str | None = None
    title: str
    author: str | None = None
    quantity_needed: int
    quantity_pledged: int
    created_at: datetime


class CampaignResponse(BaseModel):
    id: str
    created_by_user_id: str
    institution_id: str | None = None
    title: str
    description: str
    accepted_conditions: list[str]
    quantity_target: int
    quantity_pledged: int
    quantity_received: int
    pickup_address: str | None = None
    dropoff_address: str | None = None
    deadline_at: datetime | None = None
    status: CampaignStatus
    is_public: bool
    city: str | None = None
    state: str | None = None
    country: str
    needs: list[DonationNeedResponse]
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
    items: list[CampaignResponse]
    next_cursor: str | None = None


class DonationNeedImpactResponse(BaseModel):
    need_id: str
    title: str
    quantity_needed: int
    quantity_pledged: int


class CampaignImpactResponse(BaseModel):
    campaign_id: str
    quantity_target: int
    quantity_pledged: int
    quantity_received: int
    pledge_count: int
    received_pledge_count: int
    receipt_count: int
    needs: list[DonationNeedImpactResponse]


class PledgeDonationRequest(BaseModel):
    title_snapshot: str = Field(min_length=1, max_length=500)
    condition: str = Field(min_length=1, max_length=80)
    quantity: int = Field(default=1, ge=1)
    notes: str | None = Field(default=None, max_length=2000)
    donation_need_id: str | None = Field(default=None, max_length=26)

    @field_validator("title_snapshot", "condition")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class ReceiptIssueRequest(BaseModel):
    receipt_text: str = Field(min_length=1, max_length=10000)
    impact_note: str | None = Field(default=None, max_length=2000)

    @field_validator("receipt_text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("impact_note")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class DonationReceiptResponse(BaseModel):
    id: str
    pledge_id: str
    campaign_id: str
    issued_by_user_id: str
    receipt_text: str
    impact_note: str | None = None
    issued_at: datetime
    created_at: datetime


class PledgeResponse(BaseModel):
    id: str
    campaign_id: str
    donor_user_id: str
    donation_need_id: str | None = None
    title_snapshot: str
    condition: str
    quantity: int
    status: PledgeStatus
    notes: str | None = None
    accepted_at: datetime | None = None
    received_at: datetime | None = None
    receipt: DonationReceiptResponse | None = None
    created_at: datetime
    updated_at: datetime
