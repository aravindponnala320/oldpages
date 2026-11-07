from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx

from oldpages_api.core.config import Settings
from oldpages_api.identity.exceptions import ForbiddenIdentityActionError, InvalidTokenError
from oldpages_api.identity.security import normalize_email

OAuthProvider = Literal["google", "apple"]

_GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_GOOGLE_VALID_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


@dataclass(frozen=True, slots=True)
class OAuthIdentity:
    provider: OAuthProvider
    provider_account_id: str
    email: str


class OAuthProviderVerifier:
    async def verify(
        self, provider: OAuthProvider, id_token: str, settings: Settings
    ) -> OAuthIdentity:
        if provider == "google":
            return await self._verify_google(id_token, settings)
        return self._verify_dev_only(provider, id_token, settings)

    async def _verify_google(self, id_token: str, settings: Settings) -> OAuthIdentity:
        if settings.environment == "production" and not settings.google_client_id:
            raise ForbiddenIdentityActionError(
                "Google OAuth is not configured for this environment."
            )

        # Dev-mode escape hatch (same format as before) so local tests keep working
        # without a real Google ID token.
        if settings.environment != "production" and id_token.startswith("dev:google:"):
            return self._parse_dev_token("google", id_token)

        async with httpx.AsyncClient(timeout=10.0) as http:
            response = await http.get(_GOOGLE_TOKENINFO_URL, params={"id_token": id_token})

        if response.status_code != 200:
            raise InvalidTokenError("Google ID token could not be verified.")

        payload = response.json()
        issuer = str(payload.get("iss", ""))
        audience = str(payload.get("aud", ""))
        sub = str(payload.get("sub", "")).strip()
        email = normalize_email(str(payload.get("email", "")))
        email_verified = str(payload.get("email_verified", "")).lower() == "true"

        if issuer not in _GOOGLE_VALID_ISSUERS:
            raise InvalidTokenError("Google ID token has an unexpected issuer.")
        if settings.google_client_id and audience != settings.google_client_id:
            raise InvalidTokenError("Google ID token audience does not match this app.")
        if not sub or "@" not in email:
            raise InvalidTokenError("Google ID token did not include a valid identity.")
        if not email_verified:
            raise ForbiddenIdentityActionError(
                "This Google account's email is not verified with Google."
            )

        return OAuthIdentity(provider="google", provider_account_id=sub, email=email)

    def _verify_dev_only(
        self, provider: OAuthProvider, id_token: str, settings: Settings
    ) -> OAuthIdentity:
        # Apple etc. not wired up yet. Fall back to the dev-token format for local testing.
        if settings.environment == "production":
            raise ForbiddenIdentityActionError(
                f"OAuth provider '{provider}' is not configured for production."
            )
        return self._parse_dev_token(provider, id_token)

    @staticmethod
    def _parse_dev_token(provider: OAuthProvider, id_token: str) -> OAuthIdentity:
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
