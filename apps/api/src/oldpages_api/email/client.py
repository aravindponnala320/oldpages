from __future__ import annotations

import logging
from typing import Protocol

import httpx

from oldpages_api.core.config import Settings
from oldpages_api.email.templates import (
    RenderedEmail,
    render_password_reset,
    render_verify_email,
)

logger = logging.getLogger(__name__)


class EmailClient(Protocol):
    async def send_verification(self, *, to: str, token: str) -> None: ...
    async def send_password_reset(self, *, to: str, token: str) -> None: ...


class NoopEmailClient:
    """Logs what would be sent. Used in local/test environments."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_verification(self, *, to: str, token: str) -> None:
        url = self._verify_url(token)
        logger.info("email_noop_verification", extra={"to": to, "url": url})

    async def send_password_reset(self, *, to: str, token: str) -> None:
        url = self._reset_url(token)
        logger.info("email_noop_password_reset", extra={"to": to, "url": url})

    def _verify_url(self, token: str) -> str:
        return f"{self._settings.public_web_url.rstrip('/')}/verify-email?token={token}"

    def _reset_url(self, token: str) -> str:
        return f"{self._settings.public_web_url.rstrip('/')}/reset-password?token={token}"


class ResendEmailClient:
    """Sends emails via the Resend HTTP API."""

    _API_URL = "https://api.resend.com/emails"

    def __init__(self, settings: Settings) -> None:
        if settings.resend_api_key is None:
            raise RuntimeError("resend_api_key is required when email_provider='resend'")
        self._settings = settings
        self._api_key = settings.resend_api_key.get_secret_value()

    async def send_verification(self, *, to: str, token: str) -> None:
        rendered = render_verify_email(self._verify_url(token))
        await self._send(to=to, rendered=rendered)

    async def send_password_reset(self, *, to: str, token: str) -> None:
        rendered = render_password_reset(
            self._reset_url(token),
            self._settings.password_reset_token_minutes,
        )
        await self._send(to=to, rendered=rendered)

    def _verify_url(self, token: str) -> str:
        return f"{self._settings.public_web_url.rstrip('/')}/verify-email?token={token}"

    def _reset_url(self, token: str) -> str:
        return f"{self._settings.public_web_url.rstrip('/')}/reset-password?token={token}"

    async def _send(self, *, to: str, rendered: RenderedEmail) -> None:
        payload = {
            "from": self._settings.email_from,
            "to": [to],
            "subject": rendered.subject,
            "html": rendered.html,
            "text": rendered.text,
        }
        async with httpx.AsyncClient(timeout=10.0) as http:
            response = await http.post(
                self._API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        if response.status_code >= 300:
            logger.error(
                "email_send_failed",
                extra={
                    "to": to,
                    "subject": rendered.subject,
                    "status_code": response.status_code,
                    "body": response.text[:500],
                },
            )
            response.raise_for_status()
        logger.info("email_sent", extra={"to": to, "subject": rendered.subject})


def build_email_client(settings: Settings) -> EmailClient:
    if settings.email_provider == "resend":
        return ResendEmailClient(settings)
    return NoopEmailClient(settings)
