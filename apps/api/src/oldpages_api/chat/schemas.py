from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ChatRequestStatus = Literal["pending", "accepted", "declined", "blocked"]
ConversationStatus = Literal["active", "blocked", "closed"]
ConversationMemberRole = Literal["requester", "recipient"]
ConversationMemberStatus = Literal["active", "muted", "archived", "blocked"]
MessageType = Literal["text", "image", "listing", "system"]
AttachmentType = Literal["image"]


class ChatRequestCreateRequest(BaseModel):
    listing_id: str = Field(min_length=1, max_length=26)
    message: str | None = Field(default=None, max_length=2000)

    @field_validator("message")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class ChatRequestActionRequest(BaseModel):
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class UserSummary(BaseModel):
    id: str
    display_name: str | None = None
    username: str | None = None


class ChatRequestResponse(BaseModel):
    conversation_id: str | None = None
    created_at: datetime
    id: str
    initial_message: str | None = None
    listing_id: str
    listing_title: str | None = None
    recipient: UserSummary
    requester: UserSummary
    responded_at: datetime | None = None
    response_message: str | None = None
    status: ChatRequestStatus


class ConversationMemberResponse(BaseModel):
    role: ConversationMemberRole
    status: ConversationMemberStatus
    user: UserSummary


class ConversationResponse(BaseModel):
    created_at: datetime
    id: str
    last_message_at: datetime | None = None
    last_message_preview: str | None = None
    listing_id: str | None = None
    listing_title: str | None = None
    members: list[ConversationMemberResponse]
    status: ConversationStatus
    unread_count: int


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    next_cursor: str | None = None


class MessageAttachmentInput(BaseModel):
    attachment_type: AttachmentType = "image"
    media_id: str = Field(min_length=1, max_length=26)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageCreateRequest(BaseModel):
    attachments: list[MessageAttachmentInput] = Field(default_factory=list, max_length=6)
    body: str | None = Field(default=None, max_length=4000)
    client_message_id: str = Field(min_length=1, max_length=120)
    listing_id: str | None = Field(default=None, max_length=26)
    message_type: MessageType = "text"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("body")
    @classmethod
    def strip_body(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_content(self) -> MessageCreateRequest:
        if self.message_type == "text" and not self.body:
            raise ValueError("Text messages require a body.")
        if self.message_type == "image" and not self.attachments:
            raise ValueError("Image messages require at least one attachment.")
        if self.message_type == "listing" and not self.listing_id:
            raise ValueError("Listing card messages require listing_id.")
        return self


class MessageAttachmentResponse(BaseModel):
    attachment_type: AttachmentType
    id: str
    media_id: str
    metadata: dict[str, Any]
    public_url: str | None = None
    sort_order: int


class MessageResponse(BaseModel):
    attachments: list[MessageAttachmentResponse]
    body: str | None = None
    client_message_id: str | None = None
    conversation_id: str
    created_at: datetime
    id: str
    listing_id: str | None = None
    message_type: MessageType
    metadata: dict[str, Any]
    read_by_user_ids: list[str]
    sender: UserSummary


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: str | None = None


class MessageReportRequest(BaseModel):
    details: str | None = Field(default=None, max_length=2000)
    reason: Literal[
        "spam",
        "scam",
        "harassment",
        "unsafe_content",
        "personal_information",
        "other",
    ]


class MessageReportResponse(BaseModel):
    created_at: datetime
    id: str
    message_id: str
    reason: str
    status: str


class WebSocketReplayMessage(BaseModel):
    message: MessageResponse
    type: Literal["message.created"] = "message.created"

    model_config = ConfigDict(extra="forbid")
