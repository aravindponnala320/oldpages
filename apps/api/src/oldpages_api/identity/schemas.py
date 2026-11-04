from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from oldpages_api.identity.security import normalize_email

_USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9_.-]{2,39}$")


class AuthenticatedRequestContext(BaseModel):
    ip_address: str | None = None
    user_agent: str | None = None


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=12, max_length=256)
    display_name: str = Field(min_length=1, max_length=120)
    username: str | None = Field(default=None, min_length=3, max_length=40)
    terms_accepted: bool
    privacy_accepted: bool

    @field_validator("email")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        normalized = normalize_email(value)
        if "@" not in normalized:
            raise ValueError("Email address is invalid.")
        return normalized

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not _USERNAME_PATTERN.match(value):
            raise ValueError("Username must be 3-40 characters and URL-safe.")
        return value

    @model_validator(mode="after")
    def validate_consents(self) -> RegisterRequest:
        if not self.terms_accepted or not self.privacy_accepted:
            raise ValueError("Terms and privacy policy must be accepted.")
        return self


class LoginRequest(BaseModel):
    email: str
    password: str
    device_name: str | None = Field(default=None, max_length=120)
    device_type: str | None = Field(default=None, max_length=40)
    device_fingerprint: str | None = Field(default=None, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)


class TokenPair(BaseModel):
    access_token: str
    expires_in_seconds: int
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105


class DevelopmentToken(BaseModel):
    delivery: Literal["development", "out_of_band"]
    token: str | None = None


class AuthUser(BaseModel):
    email: str
    email_verified: bool
    id: str
    status: str


class AuthResponse(BaseModel):
    tokens: TokenPair
    user: AuthUser
    email_verification: DevelopmentToken | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=20)


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def normalize_email_value(cls, value: str) -> str:
        return normalize_email(value)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=12, max_length=256)


class RequestAcceptedResponse(BaseModel):
    accepted: bool
    development_token: DevelopmentToken | None = None


class MobileVerificationRequest(BaseModel):
    mobile_number: str = Field(min_length=6, max_length=32)


class OAuthRequest(BaseModel):
    id_token: str = Field(min_length=8)
    expected_email: str | None = None
    device_name: str | None = Field(default=None, max_length=120)
    device_type: str | None = Field(default=None, max_length=40)
    device_fingerprint: str | None = Field(default=None, max_length=128)

    @field_validator("expected_email")
    @classmethod
    def normalize_expected_email(cls, value: str | None) -> str | None:
        return normalize_email(value) if value else value


class SessionResponse(BaseModel):
    created_at: datetime
    current: bool = False
    id: str
    last_used_at: datetime
    revoked_at: datetime | None = None
    user_agent: str | None = None


class DeviceResponse(BaseModel):
    created_at: datetime
    device_name: str | None = None
    device_type: str | None = None
    id: str
    last_seen_at: datetime | None = None


class UserPrivateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bio: str | None
    course_department: str | None
    display_name: str
    email: str
    email_verified: bool
    favorite_authors: list[str]
    favorite_books: list[str]
    favorite_genres: list[str]
    id: str
    institution: str | None
    languages: list[str]
    mobile_verified: bool
    preferences: dict[str, str | bool]
    privacy: dict[str, str | bool]
    profile_image_url: str | None
    reading_interests: list[str]
    status: str
    username: str | None


class UserPublicResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approximate_location: str | None = None
    bio: str | None = None
    display_name: str
    id: str
    institution: str | None = None
    privacy_level: str
    profile_image_url: str | None = None
    username: str | None = None
    verification_badges: list[str]


class UpdateMeRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    username: str | None = Field(default=None, min_length=3, max_length=40)
    profile_image_url: str | None = Field(default=None, max_length=1000)
    bio: str | None = Field(default=None, max_length=2000)
    approximate_location: str | None = Field(default=None, max_length=160)
    institution: str | None = Field(default=None, max_length=160)
    course_department: str | None = Field(default=None, max_length=160)
    privacy_level: Literal["public", "members_only", "private"] | None = None
    hide_location: bool | None = None
    hide_institution: bool | None = None
    hide_followers: bool | None = None
    hide_shelves: bool | None = None
    allow_messages_from: Literal["everyone", "members", "none"] | None = None
    show_online_status: bool | None = None
    show_read_receipts: bool | None = None
    languages: list[str] | None = None
    favorite_genres: list[str] | None = None
    favorite_authors: list[str] | None = None
    favorite_books: list[str] | None = None
    reading_interests: list[str] | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not _USERNAME_PATTERN.match(value):
            raise ValueError("Username must be 3-40 characters and URL-safe.")
        return value


class BlockRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=280)


class BlockResponse(BaseModel):
    blocked_user_id: str
    id: str
