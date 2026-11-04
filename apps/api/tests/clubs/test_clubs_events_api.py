from __future__ import annotations

from typing import Any, cast

import pytest
from httpx import AsyncClient

from conftest import RegisterUser


@pytest.mark.asyncio
async def test_book_club_voting_selects_deterministically_and_links_marketplace_listings(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user(client, email="club-owner@example.com", username="club-owner")
    voter = await register_user(client, email="club-voter@example.com", username="club-voter")
    owner_token = owner["tokens"]["access_token"]
    voter_token = voter["tokens"]["access_token"]
    selected_book = await create_book(client, owner_token, title="Selected Club Book")
    other_book = await create_book(client, owner_token, title="Other Club Book")
    listing = await create_published_listing(client, owner_token, selected_book["id"])
    club = await create_club(client, owner_token, name="Deterministic Club", slug="det-club")
    first_nomination = await create_nomination(client, owner_token, club["id"], selected_book["id"])
    second_nomination = await create_nomination(client, owner_token, club["id"], other_book["id"])

    first_vote = await client.post(
        f"/api/v1/clubs/{club['id']}/votes",
        headers=auth(voter_token),
        json={"cycle_key": "summer", "nomination_id": first_nomination["id"], "rank": 1},
    )
    second_vote = await client.post(
        f"/api/v1/clubs/{club['id']}/votes",
        headers=auth(voter_token),
        json={"cycle_key": "summer", "nomination_id": second_nomination["id"], "rank": 2},
    )
    selected = await client.post(
        f"/api/v1/clubs/{club['id']}/select-book",
        headers=auth(owner_token),
        json={"cycle_key": "summer", "status": "next"},
    )

    assert first_vote.status_code == 200, first_vote.text
    assert second_vote.status_code == 200, second_vote.text
    assert selected.status_code == 200, selected.text
    assert selected.json()["book"]["id"] == selected_book["id"]
    assert [item["id"] for item in selected.json()["available_listings"]] == [listing["id"]]


@pytest.mark.asyncio
async def test_spoiler_content_is_hidden_based_on_reader_progress(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user(client, email="spoiler-owner@example.com", username="spoiler-own")
    token = owner["tokens"]["access_token"]
    book = await create_book(client, token, title="Spoiler Book")
    club = await create_club(client, token, name="Spoiler Club", slug="spoiler-club")
    club_book = await add_club_book(client, token, club["id"], book["id"])
    milestone = await client.post(
        f"/api/v1/club-books/{club_book['id']}/milestones",
        headers=auth(token),
        json={
            "discussion_prompt": "The reveal changes everything.",
            "position_type": "page",
            "position_value": 100,
            "title": "Midpoint reveal",
        },
    )

    locked = await client.get(
        f"/api/v1/club-books/{club_book['id']}/milestones",
        params={"progress_type": "page", "progress_value": 50},
    )
    unlocked = await client.get(
        f"/api/v1/club-books/{club_book['id']}/milestones",
        params={"progress_type": "page", "progress_value": 100},
    )

    assert milestone.status_code == 200, milestone.text
    assert locked.status_code == 200
    assert locked.json()["items"][0]["spoiler_locked"] is True
    assert locked.json()["items"][0]["discussion_prompt"] is None
    assert unlocked.status_code == 200
    assert unlocked.json()["items"][0]["spoiler_locked"] is False
    assert unlocked.json()["items"][0]["discussion_prompt"] == "The reveal changes everything."


@pytest.mark.asyncio
async def test_event_capacity_waitlist_promotes_when_capacity_increases(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    organizer = await register_user(client, email="event-org@example.com", username="event-org")
    first = await register_user(client, email="event-first@example.com", username="event-first")
    second = await register_user(client, email="event-second@example.com", username="event-second")
    event = await create_event(client, organizer["tokens"]["access_token"], capacity=1)

    first_rsvp = await client.post(
        f"/api/v1/events/{event['id']}/rsvps",
        headers=auth(first["tokens"]["access_token"]),
        json={},
    )
    second_rsvp = await client.post(
        f"/api/v1/events/{event['id']}/rsvps",
        headers=auth(second["tokens"]["access_token"]),
        json={},
    )
    expanded = await client.patch(
        f"/api/v1/events/{event['id']}",
        headers=auth(organizer["tokens"]["access_token"]),
        json={"capacity": 2},
    )
    second_after = await client.post(
        f"/api/v1/events/{event['id']}/rsvps",
        headers=auth(second["tokens"]["access_token"]),
        json={},
    )

    assert first_rsvp.status_code == 200, first_rsvp.text
    assert first_rsvp.json()["status"] == "going"
    assert second_rsvp.status_code == 200, second_rsvp.text
    assert second_rsvp.json()["status"] == "waitlisted"
    assert second_rsvp.json()["waitlist_position"] == 1
    assert expanded.status_code == 200, expanded.text
    assert expanded.json()["rsvp_count"] == 2
    assert expanded.json()["waitlist_count"] == 0
    assert second_after.status_code == 200
    assert second_after.json()["status"] == "going"


@pytest.mark.asyncio
async def test_event_timezone_calendar_export_and_qr_checkin(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    organizer = await register_user(
        client,
        email="tz-organizer@example.com",
        username="tz-organizer",
    )
    attendee = await register_user(client, email="tz-attendee@example.com", username="tz-attendee")
    organizer_token = organizer["tokens"]["access_token"]
    event = await create_event(client, organizer_token, timezone="Asia/Kolkata")
    rsvp = await client.post(
        f"/api/v1/events/{event['id']}/rsvps",
        headers=auth(attendee["tokens"]["access_token"]),
        json={},
    )
    calendar = await client.get(f"/api/v1/events/{event['id']}/calendar.ics")
    checkin = await client.post(
        f"/api/v1/events/{event['id']}/checkins",
        headers=auth(organizer_token),
        json={"checkin_code": event["checkin_code"], "user_id": attendee["user"]["id"]},
    )

    assert event["timezone"] == "Asia/Kolkata"
    assert event["checkin_code"] is not None
    assert rsvp.status_code == 200, rsvp.text
    assert calendar.status_code == 200, calendar.text
    assert "DTSTART;TZID=Asia/Kolkata:20260701T190000" in calendar.text
    assert checkin.status_code == 200, checkin.text
    assert checkin.json()["user_id"] == attendee["user"]["id"]


@pytest.mark.asyncio
async def test_buddy_read_progress_and_readalong_creation(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    host = await register_user(client, email="buddy-host@example.com", username="buddy-host")
    friend = await register_user(client, email="buddy-friend@example.com", username="buddy-friend")
    host_token = host["tokens"]["access_token"]
    friend_token = friend["tokens"]["access_token"]
    book = await create_book(client, host_token, title="Shared Read")

    buddy = await client.post(
        "/api/v1/buddy-reads",
        headers=auth(host_token),
        json={"book_id": book["id"], "max_participants": 3, "title": "Shared Read Sprint"},
    )
    joined = await client.post(
        f"/api/v1/buddy-reads/{buddy.json()['id']}/join",
        headers=auth(friend_token),
    )
    progress = await client.post(
        f"/api/v1/buddy-reads/{buddy.json()['id']}/progress",
        headers=auth(friend_token),
        json={"position_type": "page", "position_value": 42},
    )
    readalong = await client.post(
        "/api/v1/readalongs",
        headers=auth(host_token),
        json={
            "book_id": book["id"],
            "chapter_schedule": [{"chapter": 1, "starts_at": "2026-07-01"}],
            "starts_at": "2026-07-01T10:00:00+00:00",
            "timezone": "UTC",
            "title": "July Readalong",
        },
    )

    assert buddy.status_code == 201, buddy.text
    assert joined.status_code == 200, joined.text
    assert friend["user"]["id"] in joined.json()["participant_user_ids"]
    assert progress.status_code == 200, progress.text
    assert progress.json()["progress"][friend["user"]["id"]]["position_value"] == 42
    assert readalong.status_code == 201, readalong.text
    assert readalong.json()["chapter_schedule"] == [{"chapter": 1, "starts_at": "2026-07-01"}]


async def create_club(
    client: AsyncClient,
    token: str,
    *,
    name: str,
    slug: str,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/clubs",
        headers=auth(token),
        json={"name": name, "slug": slug, "timezone": "UTC"},
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def add_club_book(
    client: AsyncClient,
    token: str,
    club_id: str,
    book_id: str,
) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/clubs/{club_id}/books",
        headers=auth(token),
        json={"book_id": book_id, "status": "current"},
    )
    assert response.status_code == 200, response.text
    return cast("dict[str, Any]", response.json())


async def create_nomination(
    client: AsyncClient,
    token: str,
    club_id: str,
    book_id: str,
) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/clubs/{club_id}/nominations",
        headers=auth(token),
        json={"book_id": book_id, "cycle_key": "summer"},
    )
    assert response.status_code == 200, response.text
    return cast("dict[str, Any]", response.json())


async def create_event(
    client: AsyncClient,
    token: str,
    *,
    capacity: int | None = 10,
    timezone: str = "UTC",
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/events",
        headers=auth(token),
        json={
            "capacity": capacity,
            "ends_at": "2026-07-01T20:00:00+05:30"
            if timezone == "Asia/Kolkata"
            else "2026-07-01T20:00:00+00:00",
            "event_type": "book_exchange",
            "location_name": "Community library",
            "starts_at": "2026-07-01T19:00:00+05:30"
            if timezone == "Asia/Kolkata"
            else "2026-07-01T19:00:00+00:00",
            "timezone": timezone,
            "title": "Book Exchange Evening",
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def create_book(client: AsyncClient, token: str, *, title: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/books",
        headers=auth(token),
        json={
            "authors": [{"name": "Club Author"}],
            "description": "A catalog entry for club tests.",
            "format": "paperback",
            "language": "en",
            "page_count": 250,
            "publisher": {"name": "Club Publisher"},
            "title": title,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def create_published_listing(
    client: AsyncClient,
    token: str,
    book_id: str,
) -> dict[str, Any]:
    media = await upload_media(client, token)
    create = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json={
            "book_id": book_id,
            "condition": {
                "condition": "good",
                "damage_details": "Light shelf wear.",
                "highlighting_percent": 5,
            },
            "delivery_methods": [{"method": "pickup"}],
            "description": "A club-linked active listing.",
            "images": [{"alt_text": "Actual book cover", "media_id": media["id"]}],
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
        },
    )
    assert create.status_code == 201, create.text
    publish = await client.post(
        f"/api/v1/listings/{create.json()['id']}/publish",
        headers=auth(token),
    )
    assert publish.status_code == 200, publish.text
    return cast("dict[str, Any]", publish.json())


async def upload_media(client: AsyncClient, token: str) -> dict[str, Any]:
    upload = await client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 512_000, "content_type": "image/jpeg", "filename": "club.jpg"},
    )
    assert upload.status_code == 200, upload.text
    complete = await client.post(
        f"/api/v1/media/{upload.json()['id']}/complete",
        headers=auth(token),
        json={"byte_size": 512_000},
    )
    assert complete.status_code == 200, complete.text
    return cast("dict[str, Any]", complete.json())


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
