from __future__ import annotations

import pytest
from httpx import AsyncClient

from conftest import RegisterUser
from helpers import auth


@pytest.mark.asyncio
async def test_institution_verification_and_membership_require_admin(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user(
        client,
        email="institution-owner@example.com",
        username="institution-owner",
    )
    member = await register_user(
        client,
        email="institution-member@example.com",
        username="institution-member",
    )
    stranger = await register_user(
        client,
        email="institution-stranger@example.com",
        username="institution-stranger",
    )
    owner_token = owner["tokens"]["access_token"]
    member_token = member["tokens"]["access_token"]
    stranger_token = stranger["tokens"]["access_token"]

    institution_response = await client.post(
        "/api/v1/institutions",
        headers=auth(owner_token),
        json={
            "city": "Pune",
            "name": "Pune City Library",
            "state": "Maharashtra",
            "type": "library",
            "website": "https://library.test",
        },
    )
    assert institution_response.status_code == 201, institution_response.text
    institution = institution_response.json()
    assert institution["status"] == "pending"
    assert institution["is_verified"] is False

    domain_response = await client.post(
        f"/api/v1/institutions/{institution['id']}/domains",
        headers=auth(owner_token),
        json={"domain": "LIBRARY.TEST"},
    )
    assert domain_response.status_code == 201, domain_response.text
    assert domain_response.json()["domain"] == "library.test"
    assert domain_response.json()["is_verified"] is False

    forbidden_domain_verify = await client.post(
        f"/api/v1/institutions/{institution['id']}/domains/library.test/verify",
        headers=auth(stranger_token),
    )
    assert forbidden_domain_verify.status_code == 403

    domain_verify = await client.post(
        f"/api/v1/institutions/{institution['id']}/domains/library.test/verify",
        headers=auth(owner_token),
    )
    assert domain_verify.status_code == 200, domain_verify.text
    assert domain_verify.json()["is_verified"] is True

    forbidden_verify = await client.post(
        f"/api/v1/institutions/{institution['id']}/verify",
        headers=auth(stranger_token),
    )
    assert forbidden_verify.status_code == 403

    verify_response = await client.post(
        f"/api/v1/institutions/{institution['id']}/verify",
        headers=auth(owner_token),
    )
    assert verify_response.status_code == 200, verify_response.text
    assert verify_response.json()["is_verified"] is True
    assert verify_response.json()["status"] == "active"

    join_response = await client.post(
        f"/api/v1/institutions/{institution['id']}/join",
        headers=auth(member_token),
        json={"role": "member"},
    )
    assert join_response.status_code == 201, join_response.text
    assert join_response.json()["status"] == "pending"

    forbidden_members = await client.get(
        f"/api/v1/institutions/{institution['id']}/members",
        headers=auth(stranger_token),
    )
    assert forbidden_members.status_code == 403

    approve_response = await client.post(
        f"/api/v1/institutions/{institution['id']}/approve-member",
        headers=auth(owner_token),
        json={"user_id": member["user"]["id"]},
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["status"] == "active"
