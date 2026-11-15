from __future__ import annotations

import logging

import pytest

from oldpages_api.core.config import Settings
from oldpages_api.email.client import NoopEmailClient, mask_email


def test_mask_email_hides_the_mailbox() -> None:
    assert mask_email("aravind@example.com") == "a***@example.com"
    assert mask_email("not-an-address") == "***"


@pytest.mark.asyncio
async def test_reset_links_never_reach_deployed_logs(caplog: pytest.LogCaptureFixture) -> None:
    deployed = Settings.model_construct(environment="production", public_web_url="https://x.in")
    with caplog.at_level(logging.INFO, logger="oldpages_api.email.client"):
        await NoopEmailClient(deployed).send_password_reset(to="me@example.com", token="secret")

    logged = " ".join(f"{r.getMessage()} {r.__dict__}" for r in caplog.records)
    assert "secret" not in logged
    assert "me@example.com" not in logged
    assert "email_noop_password_reset_suppressed" in logged
