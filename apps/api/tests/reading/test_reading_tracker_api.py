from __future__ import annotations

from typing import Any, cast

import pytest
from httpx import AsyncClient

from conftest import RegisterUser


@pytest.mark.asyncio
async def test_progress_updates_are_idempotent_and_sync_system_shelf(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    user = await register_user(client, email="reader-progress@example.com", username="read-prog")
    token = user["tokens"]["access_token"]
    book = await create_book(client, token, title="Progress Book", page_count=200)
    payload = {
        "current_page": 40,
        "progressed_on": "2026-07-01",
        "reading_minutes": 30,
        "started_on": "2026-07-01",
        "status": "currently_reading",
    }

    first = await client.put(
        f"/api/v1/reading/progress/{book['id']}",
        headers=auth(token),
        json=payload,
    )
    second = await client.put(
        f"/api/v1/reading/progress/{book['id']}",
        headers=auth(token),
        json=payload,
    )
    progress = await client.get("/api/v1/reading/progress", headers=auth(token))
    shelves = await client.get("/api/v1/reading/shelves", headers=auth(token))

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["percent_complete"] == 20
    assert second.json()["daily_minutes"] == {"2026-07-01": 30}
    assert second.json()["total_reading_minutes"] == 30
    assert progress.status_code == 200
    assert len(progress.json()["items"]) == 1
    currently_reading = next(
        shelf for shelf in shelves.json()["items"] if shelf["slug"] == "currently-reading"
    )
    assert [item["book"]["id"] for item in currently_reading["items"]] == [book["id"]]


@pytest.mark.asyncio
async def test_private_notes_never_appear_publicly(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    user = await register_user(client, email="note-reader@example.com", username="note-reader")
    token = user["tokens"]["access_token"]
    book = await create_book(client, token, title="Notes Book", page_count=150)

    private_note = await client.post(
        "/api/v1/reading/notes",
        headers=auth(token),
        json={
            "body": "Private thought.",
            "book_id": book["id"],
            "client_note_id": "private-note-1",
            "visibility": "private",
        },
    )
    duplicate_private_note = await client.post(
        "/api/v1/reading/notes",
        headers=auth(token),
        json={
            "body": "Private thought.",
            "book_id": book["id"],
            "client_note_id": "private-note-1",
            "visibility": "private",
        },
    )
    public_note = await client.post(
        "/api/v1/reading/notes",
        headers=auth(token),
        json={
            "body": "Public quote.",
            "book_id": book["id"],
            "note_type": "quote",
            "visibility": "public",
        },
    )

    own_notes = await client.get("/api/v1/reading/notes", headers=auth(token))
    public_notes = await client.get(f"/api/v1/users/{user['user']['id']}/reading-notes")

    assert private_note.status_code == 201, private_note.text
    assert duplicate_private_note.status_code == 201, duplicate_private_note.text
    assert duplicate_private_note.json()["id"] == private_note.json()["id"]
    assert public_note.status_code == 201, public_note.text
    assert {item["body"] for item in own_notes.json()["items"]} == {
        "Private thought.",
        "Public quote.",
    }
    assert [item["body"] for item in public_notes.json()["items"]] == ["Public quote."]


@pytest.mark.asyncio
async def test_statistics_can_be_recomputed_without_duplicates(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    user = await register_user(client, email="stats-reader@example.com", username="stats-reader")
    token = user["tokens"]["access_token"]
    book = await create_book(client, token, title="Stats Book", page_count=220)
    await client.put(
        f"/api/v1/reading/progress/{book['id']}",
        headers=auth(token),
        json={
            "current_page": 100,
            "progressed_on": "2026-07-01",
            "reading_minutes": 25,
            "started_on": "2026-07-01",
            "status": "currently_reading",
        },
    )
    await client.put(
        f"/api/v1/reading/progress/{book['id']}",
        headers=auth(token),
        json={
            "current_page": 220,
            "finished_on": "2026-07-02",
            "progressed_on": "2026-07-02",
            "reading_minutes": 35,
            "started_on": "2026-07-01",
            "status": "finished",
        },
    )

    first = await client.post(
        "/api/v1/reading/statistics/recompute",
        headers=auth(token),
        json={"period_start": "2026-01-01", "period_type": "year", "timezone": "Asia/Kolkata"},
    )
    second = await client.post(
        "/api/v1/reading/statistics/recompute",
        headers=auth(token),
        json={"period_start": "2026-01-01", "period_type": "year", "timezone": "Asia/Kolkata"},
    )
    statistics = await client.get("/api/v1/reading/statistics", headers=auth(token))

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["books_completed"] == 1
    assert second.json()["pages_read"] == 220
    assert second.json()["minutes_read"] == 60
    assert second.json()["reading_streak_days"] == 2
    assert len(statistics.json()["items"]) == 1


@pytest.mark.asyncio
async def test_reading_goals_validate_timezones_and_challenge_membership(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user(client, email="goal-owner@example.com", username="goal-owner")
    member = await register_user(client, email="goal-member@example.com", username="goal-member")
    community = await create_community(
        client,
        owner["tokens"]["access_token"],
        name="Goal Readers",
        slug="goal-readers",
    )

    rejected = await client.post(
        "/api/v1/reading/goals",
        headers=auth(member["tokens"]["access_token"]),
        json={
            "community_id": community["id"],
            "goal_type": "community_challenge",
            "period_end": "2026-12-31",
            "period_start": "2026-01-01",
            "scope": "community",
            "target_value": 12,
            "timezone": "Asia/Kolkata",
        },
    )
    join = await client.post(
        f"/api/v1/communities/{community['id']}/join",
        headers=auth(member["tokens"]["access_token"]),
        json={"answers": {}},
    )
    accepted = await client.post(
        "/api/v1/reading/goals",
        headers=auth(member["tokens"]["access_token"]),
        json={
            "community_id": community["id"],
            "goal_type": "community_challenge",
            "period_end": "2026-12-31",
            "period_start": "2026-01-01",
            "scope": "community",
            "target_value": 12,
            "timezone": "Asia/Kolkata",
        },
    )
    invalid_timezone = await client.post(
        "/api/v1/reading/goals",
        headers=auth(member["tokens"]["access_token"]),
        json={
            "goal_type": "books_per_year",
            "period_end": "2026-12-31",
            "period_start": "2026-01-01",
            "target_value": 12,
            "timezone": "Not/AZone",
        },
    )

    assert rejected.status_code == 403
    assert join.status_code == 200, join.text
    assert join.json()["status"] == "active"
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["community_id"] == community["id"]
    assert accepted.json()["timezone"] == "Asia/Kolkata"
    assert invalid_timezone.status_code == 422


async def create_book(
    client: AsyncClient,
    token: str,
    *,
    page_count: int,
    title: str,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/books",
        headers=auth(token),
        json={
            "authors": [{"name": "Reading Author"}],
            "description": "A catalog entry for reading tracker tests.",
            "format": "paperback",
            "genres": ["Literary Fiction"],
            "language": "en",
            "page_count": page_count,
            "publisher": {"name": "Reading Publisher"},
            "title": title,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def create_community(
    client: AsyncClient,
    token: str,
    *,
    name: str,
    slug: str,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/communities",
        headers=auth(token),
        json={
            "community_type": "reading_goal",
            "name": name,
            "slug": slug,
            "visibility": "public",
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
