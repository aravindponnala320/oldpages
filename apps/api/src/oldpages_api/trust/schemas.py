from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ReportTargetType = Literal["user", "listing", "message", "review", "copyright"]
ReportSeverity = Literal["low", "medium", "high", "critical"]
ReportStatus = Literal["open", "in_review", "resolved", "dismissed", "appealed"]
ModerationCaseStatus = Literal["open", "in_review", "actioned", "closed", "appealed"]
ModerationActionType = Literal[
    "warn",
    "remove_content",
    "suspend",
    "ban",
    "dismiss",
    "restore",
    "appeal_submitted",
    "note",
]
RiskStatus = Literal["open", "reviewed", "cleared"]
DeviceRiskLevel = Literal["low", "medium", "high", "blocked"]
CopyrightClaimStatus = Literal["submitted", "reviewing", "actioned", "rejected"]


class TrustUserSummary(BaseModel):
    id: str


class CopyrightClaimInput(BaseModel):
    claimant_email: str = Field(min_length=3, max_length=320)
    claimant_statement: str = Field(min_length=1, max_length=4000)
    work_title: str = Field(min_length=1, max_length=500)

    @field_validator("claimant_statement", "work_title")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ReportCreateRequest(BaseModel):
    copyright_claim: CopyrightClaimInput | None = None
    description: str | None = Field(default=None, max_length=4000)
    device_fingerprint: str | None = Field(default=None, max_length=128)
    evidence: dict[str, Any] = Field(default_factory=dict)
    reason: Literal[
        "fake_listing",
        "misleading_condition",
        "piracy",
        "counterfeit",
        "scam",
        "harassment",
        "hate_speech",
        "sexual_content",
        "child_safety",
        "spam",
        "fake_review",
        "payment_fraud",
        "stolen_image",
        "copyright_infringement",
        "personal_information",
        "dangerous_meetup",
        "other",
    ]
    target_id: str | None = Field(default=None, max_length=26)
    target_type: ReportTargetType

    @field_validator("description", "device_fingerprint")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_target(self) -> ReportCreateRequest:
        if self.target_type != "copyright" and not self.target_id:
            raise ValueError("target_id is required unless target_type is copyright.")
        if self.reason == "copyright_infringement" and self.copyright_claim is None:
            raise ValueError("copyright_claim is required for copyright reports.")
        return self


class ReportAppealRequest(BaseModel):
    statement: str = Field(min_length=1, max_length=4000)

    @field_validator("statement")
    @classmethod
    def strip_statement(cls, value: str) -> str:
        return value.strip()


class ModerationActionRequest(BaseModel):
    action_type: Literal["warn", "remove_content", "suspend", "ban", "dismiss", "restore", "note"]
    duration_until: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(default=None, max_length=4000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class TargetSummary(BaseModel):
    id: str | None = None
    type: ReportTargetType


class ReportResponse(BaseModel):
    case_id: str | None = None
    created_at: datetime
    description: str | None = None
    evidence: dict[str, Any]
    id: str
    reason: str
    reporter: TrustUserSummary
    severity: ReportSeverity
    status: ReportStatus
    target: TargetSummary


class ModerationActionResponse(BaseModel):
    action_type: ModerationActionType
    actor_user_id: str | None = None
    created_at: datetime
    duration_until: datetime | None = None
    evidence_snapshot: dict[str, Any]
    id: str
    metadata: dict[str, Any]
    moderator_user_id: str | None = None
    reason: str | None = None


class ModerationCaseResponse(BaseModel):
    actions: list[ModerationActionResponse]
    assigned_moderator_user_id: str | None = None
    created_at: datetime
    evidence_snapshot: dict[str, Any]
    id: str
    priority_score: int
    report: ReportResponse
    severity: ReportSeverity
    status: ModerationCaseStatus
    summary: str


class ModerationCaseListResponse(BaseModel):
    items: list[ModerationCaseResponse]
    next_cursor: str | None = None


class ConversationEvidenceMessage(BaseModel):
    body: str | None = None
    created_at: datetime
    id: str
    message_type: str
    sender_user_id: str


class ConversationEvidenceResponse(BaseModel):
    case_id: str
    conversation_id: str
    messages: list[ConversationEvidenceMessage]
    report_id: str


class ModerationUserResponse(BaseModel):
    email: str
    id: str
    report_count: int
    status: str


class ModerationListingResponse(BaseModel):
    id: str
    report_count: int
    seller_user_id: str
    status: str
    title: str


class ModerationRuleConfigResponse(BaseModel):
    action_types: list[str]
    moderator_roles: list[str]
    severity_by_reason: dict[str, ReportSeverity]


class RiskEventResponse(BaseModel):
    created_at: datetime
    event_type: str
    id: str
    score: int
    severity: ReportSeverity
    status: RiskStatus
    user_id: str | None = None


class DeviceRiskResponse(BaseModel):
    device_fingerprint: str
    id: str
    reasons: list[str]
    risk_level: DeviceRiskLevel
    score: int
    user_id: str | None = None


class CopyrightClaimResponse(BaseModel):
    claimant_email: str
    created_at: datetime
    id: str
    report_id: str | None = None
    status: CopyrightClaimStatus
    work_title: str
