from __future__ import annotations

import pytest
from httpx import AsyncClient

from conftest import RegisterUser
from helpers import auth


@pytest.mark.asyncio
async def test_donation_conditions_and_recipient_confirmation_are_enforced(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    recipient = await register_user(
        client,
        email="donation-recipient@example.com",
        username="donation-recipient",
    )
    donor = await register_user(
        client,
        email="donation-donor@example.com",
        username="donation-donor",
    )
    recipient_token = recipient["tokens"]["access_token"]
    donor_token = donor["tokens"]["access_token"]

    campaign_response = await client.post(
        "/api/v1/donations/campaigns",
        headers=auth(recipient_token),
        json={
            "accepted_conditions": ["good", "like_new"],
            "city": "Pune",
            "description": "Collecting school books for a community library.",
            "is_public": True,
            "needs": [{"quantity_needed": 3, "title": "Grade 8 Mathematics"}],
            "quantity_target": 3,
            "state": "Maharashtra",
            "title": "Community Library Drive",
        },
    )
    assert campaign_response.status_code == 201, campaign_response.text
    campaign_id = campaign_response.json()["id"]
    need_id = campaign_response.json()["needs"][0]["id"]

    publish_response = await client.post(
        f"/api/v1/donations/campaigns/{campaign_id}/publish",
        headers=auth(recipient_token),
    )
    assert publish_response.status_code == 200, publish_response.text

    rejected_pledge = await client.post(
        f"/api/v1/donations/campaigns/{campaign_id}/pledge",
        headers=auth(donor_token),
        json={
            "condition": "poor",
            "donation_need_id": need_id,
            "quantity": 1,
            "title_snapshot": "Grade 8 Mathematics",
        },
    )
    assert rejected_pledge.status_code == 422

    pledge_response = await client.post(
        f"/api/v1/donations/campaigns/{campaign_id}/pledge",
        headers=auth(donor_token),
        json={
            "condition": "good",
            "donation_need_id": need_id,
            "quantity": 1,
            "title_snapshot": "Grade 8 Mathematics",
        },
    )
    assert pledge_response.status_code == 201, pledge_response.text
    pledge_id = pledge_response.json()["id"]

    donor_received = await client.post(
        f"/api/v1/donations/campaigns/{campaign_id}/pledges/{pledge_id}/received",
        headers=auth(donor_token),
    )
    assert donor_received.status_code == 403

    accept_response = await client.post(
        f"/api/v1/donations/campaigns/{campaign_id}/pledges/{pledge_id}/accept",
        headers=auth(recipient_token),
    )
    assert accept_response.status_code == 200, accept_response.text
    assert accept_response.json()["status"] == "accepted"

    received_response = await client.post(
        f"/api/v1/donations/campaigns/{campaign_id}/pledges/{pledge_id}/received",
        headers=auth(recipient_token),
    )
    assert received_response.status_code == 200, received_response.text
    assert received_response.json()["status"] == "received"

    impact_response = await client.get(f"/api/v1/donations/campaigns/{campaign_id}/impact")
    assert impact_response.status_code == 200, impact_response.text
    impact = impact_response.json()
    assert impact["quantity_target"] == 3
    assert impact["quantity_pledged"] == 1
    assert impact["quantity_received"] == 1
    assert impact["pledge_count"] == 1
    assert impact["received_pledge_count"] == 1
    assert impact["needs"][0]["title"] == "Grade 8 Mathematics"
    assert "donor_user_id" not in impact
    assert donor["user"]["id"] not in impact_response.text
