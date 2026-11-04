from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from oldpages_api.core.config import Settings

_password_hasher = PasswordHasher()


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, VerifyMismatchError):
        return False


def hash_secret(raw_token: str, settings: Settings) -> str:
    key = settings.jwt_secret_key.get_secret_value().encode("utf-8")
    return hmac.new(key, raw_token.encode("utf-8"), hashlib.sha256).hexdigest()


def new_secret_token() -> str:
    return secrets.token_urlsafe(48)


def create_refresh_token(session_public_id: str, settings: Settings) -> tuple[str, str]:
    raw_token = f"{session_public_id}.{new_secret_token()}"
    return raw_token, hash_secret(raw_token, settings)


def create_verification_token(settings: Settings) -> tuple[str, str]:
    raw_token = new_secret_token()
    return raw_token, hash_secret(raw_token, settings)


def create_access_token(
    *,
    user_public_id: str,
    session_public_id: str,
    settings: Settings,
    now: datetime | None = None,
) -> str:
    issued_at = now or utc_now()
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "exp": expires_at,
        "iat": issued_at,
        "session_id": session_public_id,
        "sub": user_public_id,
        "token_type": "access",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    if payload.get("token_type") != "access":
        raise jwt.InvalidTokenError("Wrong token type")
    return payload
