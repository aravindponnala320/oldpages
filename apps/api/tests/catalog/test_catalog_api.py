from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.catalog.models import Category


@pytest.mark.asyncio
async def test_catalog_entry_create_read_search_and_correct(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    category_id = await create_category(session_factory, name="Indian Literature", slug="indian")
    registered = await register_user(client)
    access_token = registered["tokens"]["access_token"]

    create_response = await client.post(
        "/api/v1/books",
        headers={"Authorization": f"Bearer {access_token}"},
        json=book_payload(category_id),
    )

    assert create_response.status_code == 201, create_response.text
    book = create_response.json()
    assert book["title"] == "Godaan"
    assert book["isbn_13"] == "9780143039433"
    assert book["authors"][0]["name"] == "Munshi Premchand"
    assert book["publisher"]["name"] == "Penguin Classics"
    assert book["categories"][0]["slug"] == "indian"
    assert book["academic_metadata"]["course"] == "Hindi Literature"

    get_response = await client.get(f"/api/v1/books/{book['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["work_id"] == book["work_id"]

    search_response = await client.get("/api/v1/books", params={"query": "Premchand"})
    assert search_response.status_code == 200
    assert search_response.json()["items"][0]["id"] == book["id"]

    isbn_search_response = await client.get(
        "/api/v1/books",
        params={"isbn": "978-0-1430-3943-3"},
    )
    assert isbn_search_response.status_code == 200
    assert isbn_search_response.json()["items"][0]["id"] == book["id"]

    patch_response = await client.patch(
        f"/api/v1/books/{book['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"metadata_status": "verified", "page_count": 336},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["metadata_status"] == "verified"
    assert patch_response.json()["page_count"] == 336


@pytest.mark.asyncio
async def test_catalog_writes_require_authentication(client: AsyncClient) -> None:
    response = await client.post("/api/v1/books", json=book_payload())

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_isbn_and_duplicate_fingerprint_are_rejected(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    headers = {"Authorization": f"Bearer {registered['tokens']['access_token']}"}

    first = await client.post("/api/v1/books", headers=headers, json=book_payload())
    assert first.status_code == 201, first.text

    duplicate_isbn = await client.post("/api/v1/books", headers=headers, json=book_payload())
    assert duplicate_isbn.status_code == 409
    assert duplicate_isbn.json()["type"] == "https://oldpages.in/problems/duplicate-catalog-entry"

    no_isbn_payload = book_payload(isbn_13=None, title="Duplicate Title")
    first_no_isbn = await client.post("/api/v1/books", headers=headers, json=no_isbn_payload)
    assert first_no_isbn.status_code == 201, first_no_isbn.text

    duplicate_fingerprint = await client.post(
        "/api/v1/books",
        headers=headers,
        json=no_isbn_payload,
    )
    assert duplicate_fingerprint.status_code == 409


@pytest.mark.asyncio
async def test_resolve_isbn_uses_local_provider(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    headers = {"Authorization": f"Bearer {registered['tokens']['access_token']}"}
    create_response = await client.post("/api/v1/books", headers=headers, json=book_payload())
    assert create_response.status_code == 201, create_response.text

    found = await client.post("/api/v1/books/resolve-isbn", json={"isbn": "9780143039433"})
    assert found.status_code == 200
    assert found.json()["status"] == "found"
    assert found.json()["provider"] == "local_catalog"

    missing = await client.post("/api/v1/books/resolve-isbn", json={"isbn": "9780132350884"})
    assert missing.status_code == 200
    assert missing.json() == {
        "book": None,
        "isbn": "9780132350884",
        "provider": "local_catalog",
        "status": "not_found",
    }


@pytest.mark.asyncio
async def test_category_tree_supports_arbitrary_depth(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        root = Category(name="Academic", slug="academic", sort_order=1)
        child = Category(name="Engineering", slug="engineering", parent=root, sort_order=1)
        grandchild = Category(
            name="Computer Science",
            slug="computer-science",
            parent=child,
            sort_order=1,
        )
        session.add_all([root, child, grandchild])
        await session.commit()

    response = await client.get("/api/v1/categories")

    assert response.status_code == 200
    root_node = response.json()["items"][0]
    assert root_node["slug"] == "academic"
    assert root_node["children"][0]["slug"] == "engineering"
    assert root_node["children"][0]["children"][0]["slug"] == "computer-science"


@pytest.mark.asyncio
async def test_authors_and_publishers_are_listed(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    headers = {"Authorization": f"Bearer {registered['tokens']['access_token']}"}
    create_response = await client.post("/api/v1/books", headers=headers, json=book_payload())
    assert create_response.status_code == 201, create_response.text

    authors = await client.get("/api/v1/authors", params={"query": "Premchand"})
    publishers = await client.get("/api/v1/publishers", params={"query": "Penguin"})

    assert authors.status_code == 200
    assert publishers.status_code == 200
    assert authors.json()["items"][0]["name"] == "Munshi Premchand"
    assert publishers.json()["items"][0]["name"] == "Penguin Classics"


async def create_category(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    name: str,
    slug: str,
) -> str:
    async with session_factory() as session:
        category = Category(name=name, slug=slug)
        session.add(category)
        await session.commit()
        return category.public_id


def book_payload(
    category_id: str | None = None,
    *,
    isbn_13: str | None = "9780143039433",
    title: str = "Godaan",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "academic_metadata": {
            "course": "Hindi Literature",
            "degree": "BA",
            "subject": "Hindi",
        },
        "authors": [{"name": "Munshi Premchand"}],
        "description": "A canonical Hindi novel.",
        "edition": "Paperback",
        "format": "paperback",
        "genres": ["Literary Fiction"],
        "language": "hi",
        "page_count": 320,
        "publication_year": 2019,
        "publisher": {"name": "Penguin Classics"},
        "subjects": ["Indian literature"],
        "title": title,
    }
    if isbn_13 is not None:
        payload["isbn_13"] = isbn_13
    if category_id is not None:
        payload["category_ids"] = [category_id]
    return payload
