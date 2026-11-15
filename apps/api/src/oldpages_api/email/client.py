from __future__ import annotations

import logging
from email.utils import parseaddr
from typing import Protocol

import httpx

from oldpages_api.core.config import Settings
from oldpages_api.email.templates import (
    RenderedEmail,
    render_password_reset,
    render_verify_email,
)

logger = logging.getLogger(__name__)


def mask_email(address: str) -> str:
    """Enough to tell messages apart in logs without storing the address: a***@gmail.com."""
    local, _, domain = address.partition("@")
    return f"{local[:1]}***@{domain}" if domain else "***"


class EmailClient(Protocol):
    async def send_verification(self, *, to: str, token: str) -> None: ...
    async def send_password_reset(self, *, to: str, token: str) -> None: ...


class NoopEmailClient:
    """Logs what would be sent. Used in local/test environments."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_verification(self, *, to: str, token: str) -> None:
        self._log("email_noop_verification", to, self._verify_url(token))

    async def send_password_reset(self, *, to: str, token: str) -> None:
        self._log("email_noop_password_reset", to, self._reset_url(token))

    def _log(self, event: str, to: str, url: str) -> None:
        # The link signs whoever opens it in, so it only reaches logs on a developer's machine.
        if self._settings.environment in {"local", "test"}:
            logger.info(event, extra={"to": to, "url": url})
        else:
            logger.warning(f"{event}_suppressed", extra={"to": mask_email(to)})

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
                    "to": mask_email(to),
                    "subject": rendered.subject,
                    "status_code": response.status_code,
                    "body": response.text[:500],
                },
            )
            response.raise_for_status()
        logger.info("email_sent", extra={"to": mask_email(to), "subject": rendered.subject})


class MailjetEmailClient:
    """Sends emails via the Mailjet Send API v3.1."""

    _API_URL = "https://api.mailjet.com/v3.1/send"

    def __init__(self, settings: Settings) -> None:
        if not settings.mailjet_api_key or not settings.mailjet_secret_key:
            raise RuntimeError(
                "mailjet_api_key and mailjet_secret_key are required when email_provider='mailjet'"
            )
        self._settings = settings
        self._auth = (
            settings.mailjet_api_key.get_secret_value(),
            settings.mailjet_secret_key.get_secret_value(),
        )

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
        # Mailjet wants name and address separately; email_from is "Name <address>".
        from_name, from_email = parseaddr(self._settings.email_from)
        sender = {"Email": from_email}
        if from_name:
            sender["Name"] = from_name
        payload = {
            "SandboxMode": self._settings.mailjet_sandbox,
            "Messages": [
                {
                    "From": sender,
                    "To": [{"Email": to}],
                    "Subject": rendered.subject,
                    "HTMLPart": rendered.html,
                    "TextPart": rendered.text,
                }
            ],
        }
        async with httpx.AsyncClient(timeout=10.0) as http:
            response = await http.post(self._API_URL, json=payload, auth=self._auth)
        if response.status_code >= 300:
            logger.error(
                "email_send_failed",
                extra={
                    "to": mask_email(to),
                    "subject": rendered.subject,
                    "status_code": response.status_code,
                    "body": response.text[:500],
                },
            )
            response.raise_for_status()
        logger.info("email_sent", extra={"to": mask_email(to), "subject": rendered.subject})


def build_email_client(settings: Settings) -> EmailClient:
    if settings.email_provider == "resend":
        return ResendEmailClient(settings)
    if settings.email_provider == "mailjet":
        return MailjetEmailClient(settings)
    return NoopEmailClient(settings)
