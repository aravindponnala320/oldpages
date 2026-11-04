from __future__ import annotations

import jwt

from oldpages_api.core.config import Settings
from oldpages_api.identity.security import create_access_token, hash_password, verify_password


def test_password_hash_uses_argon2id(test_settings: Settings) -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("$argon2")
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_access_token_has_expiration(test_settings: Settings) -> None:
    token = create_access_token(
        user_public_id="01JTESTUSER0000000000000",
        session_public_id="01JTESTSESSION000000000",
        settings=test_settings,
    )

    payload = jwt.decode(
        token,
        test_settings.jwt_secret_key.get_secret_value(),
        algorithms=[test_settings.jwt_algorithm],
    )

    assert payload["token_type"] == "access"  # noqa: S105
    assert "exp" in payload
