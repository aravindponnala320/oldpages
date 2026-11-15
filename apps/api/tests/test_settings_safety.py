from __future__ import annotations

from typing import Any, Literal

import pytest
from pydantic import SecretStr, ValidationError

from oldpages_api.core.config import Settings
from oldpages_api.identity.exceptions import ForbiddenIdentityActionError, InvalidTokenError
from oldpages_api.identity.oauth import oauth_verifier

SAFE: dict[str, Any] = {
    "jwt_secret_key": SecretStr("x" * 48),
    "object_storage_secret_key": SecretStr("real-storage-secret"),
    "expose_development_auth_tokens": False,
    "public_web_url": "https://oldpages.in",
}


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_deployed_settings_must_be_safe(environment: Literal["staging", "production"]) -> None:
    Settings(environment=environment, **SAFE)  # fine

    for field, unsafe in [
        ("jwt_secret_key", SecretStr("development-only-change-me")),
        ("jwt_secret_key", SecretStr("too-short")),
        ("object_storage_secret_key", SecretStr("oldpages-secret")),
        ("expose_development_auth_tokens", True),
        ("public_web_url", "http://localhost:3000"),
    ]:
        with pytest.raises(ValidationError, match=field.upper()):
            Settings(environment=environment, **{**SAFE, field: unsafe})


def test_local_development_keeps_its_defaults() -> None:
    Settings(environment="local")


class RejectingGoogle:
    """Stands in for httpx.AsyncClient: Google says the token is not valid."""

    calls = 0

    def __init__(self, **_: object) -> None: ...

    async def __aenter__(self) -> RejectingGoogle:
        return self

    async def __aexit__(self, *_: object) -> None: ...

    async def get(self, *_: object, **__: object) -> object:
        RejectingGoogle.calls += 1
        return type("Response", (), {"status_code": 400})()


@pytest.mark.asyncio
async def test_fake_google_tokens_only_work_locally(monkeypatch: pytest.MonkeyPatch) -> None:
    import oldpages_api.identity.oauth as oauth

    monkeypatch.setattr(oauth.httpx, "AsyncClient", RejectingGoogle)
    staging = Settings(environment="staging", google_client_id="client-id", **SAFE)

    with pytest.raises(InvalidTokenError):
        await oauth_verifier.verify("google", "dev:google:1:victim@example.com", staging)
    assert RejectingGoogle.calls == 1  # sent to Google, not trusted as a dev token

    local = await oauth_verifier.verify(
        "google", "dev:google:1:me@example.com", Settings(environment="local")
    )
    assert local.email == "me@example.com"


@pytest.mark.asyncio
async def test_google_needs_a_client_id_when_deployed() -> None:
    with pytest.raises(ForbiddenIdentityActionError):
        await oauth_verifier.verify("google", "any-token", Settings(environment="staging", **SAFE))
