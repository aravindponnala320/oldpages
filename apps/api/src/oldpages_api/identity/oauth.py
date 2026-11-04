from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from oldpages_api.core.config import Settings
from oldpages_api.identity.exceptions import ForbiddenIdentityActionError, InvalidTokenError
from oldpages_api.identity.security import normalize_email

OAuthProvider = Literal["google", "apple"]


@dataclass(frozen=True, slots=True)
class OAuthIdentity:
    provider: OAuthProvider
    provider_account_id: str
    email: str


class OAuthProviderVerifier:
    async def verify(
        self, provider: OAuthProvider, id_token: str, settings: Settings
    ) -> OAuthIdentity:
        if settings.environment == "production":
            raise ForbiddenIdentityActionError(
                "Production OAuth verification is not configured yet."
            )

        parts = id_token.split(":", maxsplit=3)
        if len(parts) != 4 or parts[0] != "dev" or parts[1] != provider:
            raise InvalidTokenError("OAuth token could not be verified.")

        provider_account_id = parts[2].strip()
        email = normalize_email(parts[3])
        if not provider_account_id or "@" not in email:
            raise InvalidTokenError("OAuth token did not include a valid identity.")

        return OAuthIdentity(
            email=email,
            provider=provider,
            provider_account_id=provider_account_id,
        )


oauth_verifier = OAuthProviderVerifier()
