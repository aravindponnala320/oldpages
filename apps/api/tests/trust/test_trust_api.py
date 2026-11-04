from __future__ import annotations

from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.identity.models import AuditLog, User, UserPreference
from oldpages_api.trust.events import (
    CONVERSATION_EVIDENCE_ACCESSED,
    MODERATION_ACTION_TAKEN,
)
from oldpages_api.trust.models import (
    CopyrightClaim,
    DeviceRisk,
    ModerationAction,
    Report,
    RiskEvent,
)


@pytest.mark.asyncio
async def test_high_severity_reports_are_prioritized_and_create_risk_records(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    seller = await register_user(client, email="seller-trust@example.com", username="seller-t")
    reporter = await register_user(
        client,
        email="reporter-trust@example.com",
        username="reporter-t",
    )
    moderator = await register_user(
        client,
        email="moderator-trust@example.com",
        username="moderator-t",
    )
    await grant_moderator(session_factory, moderator["user"]["id"])
    listing = await create_published_listing(
        client,
        seller["tokens"]["access_token"],
        title="Reported Listing",
    )

    low_report = await client.post(
        "/api/v1/reports",
        headers=auth(reporter["tokens"]["access_token"]),
        json={
            "description": "Looks like spam.",
            "reason": "spam",
            "target_id": listing["id"],
            "target_type": "listing",
        },
    )
    high_report = await client.post(
        "/api/v1/reports",
        headers=auth(reporter["tokens"]["access_token"]),
        json={
            "copyright_claim": {
                "claimant_email": "rights@example.com",
                "claimant_statement": "This listing uses my protected scan.",
                "work_title": "Protected Notes",
            },
            "description": "Image appears to be copied from my work.",
            "device_fingerprint": "device-high-risk",
            "evidence": {"image_url": "https://example.test/photo.jpg"},
            "reason": "copyright_infringement",
            "target_id": listing["id"],
            "target_type": "listing",
        },
    )
    queue_response = await client.get(
        "/api/v1/admin/moderation/cases",
        headers=auth(moderator["tokens"]["access_token"]),
    )

    assert low_report.status_code == 201, low_report.text
    assert low_report.json()["severity"] == "low"
    assert high_report.status_code == 201, high_report.text
    assert high_report.json()["severity"] == "high"
    assert queue_response.status_code == 200, queue_response.text
    assert queue_response.json()["items"][0]["id"] == high_report.json()["case_id"]

    async with session_factory() as session:
        risk_event = (
            await session.execute(
                select(RiskEvent).where(RiskEvent.event_type == "report:copyright_infringement")
            )
        ).scalar_one()
        device_risk = (
            await session.execute(
                select(DeviceRisk).where(DeviceRisk.device_fingerprint == "device-high-risk")
            )
        ).scalar_one()
        copyright_claim = (
            await session.execute(
                select(CopyrightClaim).where(CopyrightClaim.claimant_email == "rights@example.com")
            )
        ).scalar_one()

    assert risk_event.severity == "high"
    assert risk_event.score == 80
    assert device_risk.risk_level == "high"
    assert device_risk.reasons_json == ["copyright_infringement"]
    assert copyright_claim.status == "submitted"


@pytest.mark.asyncio
async def test_moderator_action_is_audited_and_suspension_enforces_immediately(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    reporter = await register_user(client, email="reporter-action@example.com", username="rep-act")
    target = await register_user(client, email="target-action@example.com", username="target-act")
    moderator = await register_user(client, email="mod-action@example.com", username="mod-act")
    await grant_moderator(session_factory, moderator["user"]["id"])
    report = await create_user_report(client, reporter, target["user"]["id"], reason="scam")

    action_response = await client.post(
        f"/api/v1/admin/moderation/cases/{report['case_id']}/actions",
        headers=auth(moderator["tokens"]["access_token"]),
        json={"action_type": "suspend", "reason": "Payment fraud pattern."},
    )
    get_me_after = await client.get(
        "/api/v1/users/me",
        headers=auth(target["tokens"]["access_token"]),
    )
    login_after = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "target-action@example.com",
            "password": "correct horse battery staple",
        },
    )

    assert action_response.status_code == 200, action_response.text
    assert action_response.json()["status"] == "actioned"
    assert action_response.json()["assigned_moderator_user_id"] == moderator["user"]["id"]
    assert get_me_after.status_code == 401
    assert login_after.status_code == 401

    async with session_factory() as session:
        target_user = (
            await session.execute(select(User).where(User.public_id == target["user"]["id"]))
        ).scalar_one()
        audit_log = (
            await session.execute(
                select(AuditLog).where(AuditLog.action == MODERATION_ACTION_TAKEN)
            )
        ).scalar_one()

    assert target_user.status == "suspended"
    assert audit_log.context_json["case_id"] == report["case_id"]
    assert audit_log.context_json["action_type"] == "suspend"


@pytest.mark.asyncio
async def test_conversation_evidence_requires_case_context_and_is_audited(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    seller = await register_user(
        client,
        email="seller-evidence@example.com",
        username="seller-e",
    )
    buyer = await register_user(client, email="buyer-evidence@example.com", username="buyer-e")
    moderator = await register_user(
        client,
        email="mod-evidence@example.com",
        username="mod-e",
    )
    await grant_moderator(session_factory, moderator["user"]["id"])
    message = await accepted_conversation_message(
        client,
        seller["tokens"]["access_token"],
        buyer["tokens"]["access_token"],
    )
    message_report = await client.post(
        "/api/v1/reports",
        headers=auth(seller["tokens"]["access_token"]),
        json={
            "description": "Buyer is harassing me.",
            "reason": "harassment",
            "target_id": message["id"],
            "target_type": "message",
        },
    )
    user_report = await create_user_report(client, seller, buyer["user"]["id"], reason="scam")

    evidence_response = await client.get(
        f"/api/v1/admin/moderation/cases/{message_report.json()['case_id']}/conversation-evidence",
        headers=auth(moderator["tokens"]["access_token"]),
    )
    blocked_response = await client.get(
        f"/api/v1/admin/moderation/cases/{user_report['case_id']}/conversation-evidence",
        headers=auth(moderator["tokens"]["access_token"]),
    )

    assert message_report.status_code == 201, message_report.text
    assert evidence_response.status_code == 200, evidence_response.text
    assert evidence_response.json()["messages"][0]["id"] == message["id"]
    assert blocked_response.status_code == 403

    async with session_factory() as session:
        audit_log = (
            await session.execute(
                select(AuditLog).where(AuditLog.action == CONVERSATION_EVIDENCE_ACCESSED)
            )
        ).scalar_one()

    assert audit_log.context_json["case_id"] == message_report.json()["case_id"]


@pytest.mark.asyncio
async def test_appeals_preserve_original_evidence_snapshot(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    reporter = await register_user(
        client,
        email="reporter-appeal@example.com",
        username="rep-app",
    )
    target = await register_user(client, email="target-appeal@example.com", username="target-app")
    report = await create_user_report(
        client,
        reporter,
        target["user"]["id"],
        evidence={"original_url": "https://example.test/evidence"},
        reason="scam",
    )

    appeal_response = await client.post(
        f"/api/v1/reports/{report['id']}/appeal",
        headers=auth(reporter["tokens"]["access_token"]),
        json={"statement": "The evidence has been misunderstood."},
    )

    assert appeal_response.status_code == 200, appeal_response.text
    assert appeal_response.json()["status"] == "appealed"

    async with session_factory() as session:
        report_model = (
            await session.execute(select(Report).where(Report.public_id == report["id"]))
        ).scalar_one()
        appeal_action = (
            await session.execute(
                select(ModerationAction).where(ModerationAction.action_type == "appeal_submitted")
            )
        ).scalar_one()

    assert report_model.status == "appealed"
    assert appeal_action.evidence_snapshot_json["evidence"] == {
        "original_url": "https://example.test/evidence"
    }
    assert appeal_action.metadata_json["appeal_statement"] == (
        "The evidence has been misunderstood."
    )


async def grant_moderator(
    session_factory: async_sessionmaker[AsyncSession],
    user_public_id: str,
) -> None:
    async with session_factory() as session:
        user = (
            await session.execute(select(User).where(User.public_id == user_public_id))
        ).scalar_one()
        preference = (
            await session.execute(select(UserPreference).where(UserPreference.user_id == user.id))
        ).scalar_one()
        preference.metadata_json = {"roles": ["moderator"]}
        await session.commit()


async def create_user_report(
    client: AsyncClient,
    reporter: dict[str, Any],
    target_user_id: str,
    *,
    evidence: dict[str, Any] | None = None,
    reason: str,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/reports",
        headers=auth(reporter["tokens"]["access_token"]),
        json={
            "description": "Trust report.",
            "evidence": evidence or {},
            "reason": reason,
            "target_id": target_user_id,
            "target_type": "user",
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def accepted_conversation_message(
    client: AsyncClient,
    seller_token: str,
    buyer_token: str,
) -> dict[str, Any]:
    listing = await create_published_listing(client, seller_token, title="Evidence Chat Book")
    request_response = await client.post(
        "/api/v1/chat-requests",
        headers=auth(buyer_token),
        json={"listing_id": listing["id"], "message": "Is it available?"},
    )
    assert request_response.status_code == 201, request_response.text
    accept_response = await client.post(
        f"/api/v1/chat-requests/{request_response.json()['id']}/accept",
        headers=auth(seller_token),
        json={},
    )
    assert accept_response.status_code == 200, accept_response.text
    conversation_id = accept_response.json()["conversation_id"]
    message_response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth(buyer_token),
        json={"body": "I can pay outside the app.", "client_message_id": "evidence-1"},
    )
    assert message_response.status_code == 201, message_response.text
    return cast("dict[str, Any]", message_response.json())


async def create_published_listing(
    client: AsyncClient,
    token: str,
    *,
    title: str,
) -> dict[str, Any]:
    book = await create_book(client, token, title=title)
    media = await upload_media(client, token)
    create_response = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json=listing_payload(book_id=book["id"], image_id=media["id"]),
    )
    assert create_response.status_code == 201, create_response.text
    publish_response = await client.post(
        f"/api/v1/listings/{create_response.json()['id']}/publish",
        headers=auth(token),
    )
    assert publish_response.status_code == 200, publish_response.text
    return cast("dict[str, Any]", publish_response.json())


async def create_book(client: AsyncClient, token: str, *, title: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/books",
        headers=auth(token),
        json={
            "authors": [{"name": "Trust Author"}],
            "description": "A catalog entry for trust tests.",
            "format": "paperback",
            "language": "en",
            "page_count": 240,
            "publisher": {"name": "Trust Publisher"},
            "title": title,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def upload_media(client: AsyncClient, token: str) -> dict[str, Any]:
    upload_response = await client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 512_000, "content_type": "image/jpeg", "filename": "trust.jpg"},
    )
    assert upload_response.status_code == 200, upload_response.text
    complete_response = await client.post(
        f"/api/v1/media/{upload_response.json()['id']}/complete",
        headers=auth(token),
        json={"byte_size": 512_000},
    )
    assert complete_response.status_code == 200, complete_response.text
    return cast("dict[str, Any]", complete_response.json())


def listing_payload(*, book_id: str, image_id: str) -> dict[str, Any]:
    return {
        "book_id": book_id,
        "condition": {
            "condition": "good",
            "damage_details": "Light shelf wear.",
            "highlighting_percent": 5,
        },
        "delivery_methods": [{"method": "pickup"}],
        "description": "A clean copy for a trust flow test.",
        "images": [{"alt_text": "Actual cover", "media_id": image_id}],
        "listing_modes": ["sell"],
        "location": {
            "campus_pickup": True,
            "city": "Pune",
            "country": "IN",
            "exact_latitude": "18.520430",
            "exact_longitude": "73.856744",
            "neighborhood": "Deccan",
            "pickup_notes_private": "Meet at the library gate.",
            "public_area": "Deccan, Pune",
            "state": "Maharashtra",
        },
        "price_amount_cents": 45000,
        "quantity": 1,
    }


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
