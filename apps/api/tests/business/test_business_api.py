from __future__ import annotations

import pytest
from httpx import AsyncClient

from conftest import RegisterUser
from helpers import auth


@pytest.mark.asyncio
async def test_business_owner_controls_profile_locations_and_staff(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user(
        client,
        email="business-owner@example.com",
        username="business-owner",
    )
    staff = await register_user(
        client,
        email="business-staff@example.com",
        username="business-staff",
    )
    stranger = await register_user(
        client,
        email="business-stranger@example.com",
        username="business-stranger",
    )
    owner_token = owner["tokens"]["access_token"]
    staff_token = staff["tokens"]["access_token"]
    stranger_token = stranger["tokens"]["access_token"]

    profile_response = await client.post(
        "/api/v1/business",
        headers=auth(owner_token),
        json={"name": "Deccan Book Shop", "type": "shop", "website": "https://shop.test"},
    )
    assert profile_response.status_code == 201, profile_response.text
    profile = profile_response.json()
    assert profile["status"] == "pending"
    assert profile["slug"] == "deccan-book-shop"

    duplicate_profile = await client.post(
        "/api/v1/business",
        headers=auth(owner_token),
        json={"name": "Another Shop", "type": "shop"},
    )
    assert duplicate_profile.status_code == 422

    location_response = await client.post(
        f"/api/v1/business/{profile['id']}/locations",
        headers=auth(owner_token),
        json={
            "address": "1 Library Road",
            "city": "Pune",
            "is_primary": True,
            "name": "Main store",
            "pincode": "411004",
            "state": "Maharashtra",
        },
    )
    assert location_response.status_code == 201, location_response.text
    assert location_response.json()["is_primary"] is True

    forbidden_update = await client.patch(
        f"/api/v1/business/{profile['id']}",
        headers=auth(stranger_token),
        json={"description": "Not my profile"},
    )
    assert forbidden_update.status_code == 403

    invite_response = await client.post(
        f"/api/v1/business/{profile['id']}/staff",
        headers=auth(owner_token),
        json={"role": "manager", "user_id": staff["user"]["id"]},
    )
    duplicate_invite = await client.post(
        f"/api/v1/business/{profile['id']}/staff",
        headers=auth(owner_token),
        json={"role": "manager", "user_id": staff["user"]["id"]},
    )
    assert invite_response.status_code == 201, invite_response.text
    assert invite_response.json()["role"] == "manager"
    assert "manage_inventory" in invite_response.json()["permissions"]
    assert duplicate_invite.status_code == 409

    forbidden_staff_invite = await client.post(
        f"/api/v1/business/{profile['id']}/staff",
        headers=auth(staff_token),
        json={"role": "staff", "user_id": stranger["user"]["id"]},
    )
    assert forbidden_staff_invite.status_code == 403

    import_payload = {
        "filename": "inventory.csv",
        "idempotency_key": "inventory-import-1",
        "rows": [
            {
                "condition": "good",
                "price_amount_cents": 45000,
                "quantity": 2,
                "title": "Clean Code",
            },
            {
                "condition": "unknown",
                "price_amount_cents": -1,
                "quantity": 0,
                "title": "",
            },
        ],
    }
    import_response = await client.post(
        f"/api/v1/business/{profile['id']}/imports",
        headers=auth(staff_token),
        json=import_payload,
    )
    assert import_response.status_code == 201, import_response.text
    inventory_import = import_response.json()
    assert inventory_import["status"] == "completed"
    assert inventory_import["success_rows"] == 1
    assert inventory_import["error_rows"] == 1
    assert inventory_import["error_report_url"] is not None

    duplicate_import = await client.post(
        f"/api/v1/business/{profile['id']}/imports",
        headers=auth(staff_token),
        json=import_payload,
    )
    assert duplicate_import.status_code == 201, duplicate_import.text
    assert duplicate_import.json()["id"] == inventory_import["id"]

    error_report = await client.get(
        f"/api/v1/business/{profile['id']}/imports/{inventory_import['id']}/errors.csv",
        headers=auth(staff_token),
    )
    assert error_report.status_code == 200, error_report.text
    assert "row_number,errors,row" in error_report.text
    assert "title is required" in error_report.text
