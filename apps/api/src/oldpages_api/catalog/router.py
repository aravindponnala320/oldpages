from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.catalog.schemas import (
    AuthorListResponse,
    BookCreateRequest,
    BookListResponse,
    BookResponse,
    BookUpdateRequest,
    CategoryTreeResponse,
    PublisherListResponse,
    ResolveIsbnRequest,
    ResolveIsbnResponse,
)
from oldpages_api.catalog.service import CatalogService
from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from oldpages_api.shared.db.database import get_session

books_router = APIRouter(prefix="/books", tags=["books"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])
authors_router = APIRouter(prefix="/authors", tags=["authors"])
publishers_router = APIRouter(prefix="/publishers", tags=["publishers"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]
LimitQuery = Annotated[int, Query(ge=1, le=100)]


def catalog_service(session: AsyncSession) -> CatalogService:
    return CatalogService(session)


@books_router.get("", response_model=BookListResponse)
async def list_books(
    session: SessionDep,
    author: str | None = Query(default=None, max_length=240),
    category: str | None = Query(default=None, max_length=180),
    cursor: str | None = Query(default=None, max_length=26),
    isbn: str | None = Query(default=None, max_length=32),
    language: str | None = Query(default=None, max_length=24),
    limit: LimitQuery = 50,
    publisher: str | None = Query(default=None, max_length=240),
    query: str | None = Query(default=None, max_length=500),
) -> BookListResponse:
    return await catalog_service(session).list_books(
        author=author,
        category=category,
        cursor=cursor,
        isbn=isbn,
        language=language,
        limit=limit,
        publisher=publisher,
        query=query,
    )


@books_router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> BookResponse:
    return await catalog_service(session).create_book(
        payload,
        principal.user,
        request_context(request),
    )


@books_router.post("/resolve-isbn", response_model=ResolveIsbnResponse)
async def resolve_isbn(
    payload: ResolveIsbnRequest,
    session: SessionDep,
) -> ResolveIsbnResponse:
    return await catalog_service(session).resolve_isbn(payload.isbn)


@books_router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    session: SessionDep,
) -> BookResponse:
    return await catalog_service(session).get_book(book_id)


@books_router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: str,
    payload: BookUpdateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> BookResponse:
    return await catalog_service(session).update_book(
        book_id,
        payload,
        principal.user,
        request_context(request),
    )


@categories_router.get("", response_model=CategoryTreeResponse)
async def list_categories(session: SessionDep) -> CategoryTreeResponse:
    return await catalog_service(session).list_categories()


@authors_router.get("", response_model=AuthorListResponse)
async def list_authors(
    session: SessionDep,
    cursor: str | None = Query(default=None, max_length=26),
    limit: LimitQuery = 50,
    query: str | None = Query(default=None, max_length=240),
) -> AuthorListResponse:
    return await catalog_service(session).list_authors(
        cursor=cursor,
        limit=limit,
        query=query,
    )


@publishers_router.get("", response_model=PublisherListResponse)
async def list_publishers(
    session: SessionDep,
    cursor: str | None = Query(default=None, max_length=26),
    limit: LimitQuery = 50,
    query: str | None = Query(default=None, max_length=240),
) -> PublisherListResponse:
    return await catalog_service(session).list_publishers(
        cursor=cursor,
        limit=limit,
        query=query,
    )
