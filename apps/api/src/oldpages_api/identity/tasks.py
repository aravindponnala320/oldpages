from __future__ import annotations


async def deliver_identity_token(*, destination: str, token: str, purpose: str) -> None:
    _ = (destination, token, purpose)
    # Real email/SMS delivery starts when notification providers are introduced.
