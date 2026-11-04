from __future__ import annotations

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.elements import ColumnElement

from oldpages_api.catalog.models import (
    AcademicMetadata,
    Author,
    Book,
    BookAuthor,
    BookCategory,
    BookEdition,
    BookIdentifier,
    Category,
    Publisher,
)


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_edition_by_public_id(self, public_id: str) -> BookEdition | None:
        result = await self.session.execute(
            select(BookEdition)
            .options(*edition_load_options())
            .where(BookEdition.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_edition_by_identifier(
        self,
        identifier_type: str,
        identifier_value: str,
    ) -> BookEdition | None:
        result = await self.session.execute(
            select(BookEdition)
            .join(BookIdentifier)
            .options(*edition_load_options())
            .where(
                BookIdentifier.identifier_type == identifier_type,
                BookIdentifier.identifier_value == identifier_value,
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_edition_by_fingerprint(self, fingerprint: str) -> BookEdition | None:
        result = await self.session.execute(
            select(BookEdition)
            .options(*edition_load_options())
            .where(BookEdition.edition_fingerprint == fingerprint)
        )
        return result.scalar_one_or_none()

    async def list_book_editions(
        self,
        *,
        author: str | None,
        category: Category | None,
        cursor: str | None,
        identifier: tuple[str, str] | None,
        language: str | None,
        limit: int,
        publisher: str | None,
        query: str | None,
    ) -> tuple[list[BookEdition], str | None]:
        statement = select(BookEdition).options(*edition_load_options())
        statement = statement.order_by(BookEdition.id.desc()).limit(limit + 1)

        if cursor:
            cursor_edition = await self.get_edition_by_public_id(cursor)
            if cursor_edition is not None:
                statement = statement.where(BookEdition.id < cursor_edition.id)

        statement = apply_book_filters(
            statement,
            author=author,
            category=category,
            identifier=identifier,
            language=language,
            publisher=publisher,
            query=query,
        )
        result = await self.session.execute(statement)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[limit].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def get_author_by_normalized_name(self, normalized_name: str) -> Author | None:
        result = await self.session.execute(
            select(Author).where(Author.normalized_name == normalized_name)
        )
        return result.scalar_one_or_none()

    async def list_authors(
        self,
        *,
        cursor: str | None,
        limit: int,
        query: str | None,
    ) -> tuple[list[Author], str | None]:
        statement = select(Author).order_by(Author.id.desc()).limit(limit + 1)
        if cursor:
            cursor_author = await self.get_author_by_public_id(cursor)
            if cursor_author is not None:
                statement = statement.where(Author.id < cursor_author.id)
        if query:
            statement = statement.where(Author.name.ilike(f"%{query.strip()}%"))
        result = await self.session.execute(statement)
        rows = list(result.scalars().all())
        next_cursor = rows[limit].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def get_author_by_public_id(self, public_id: str) -> Author | None:
        result = await self.session.execute(select(Author).where(Author.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_publisher_by_normalized_name(self, normalized_name: str) -> Publisher | None:
        result = await self.session.execute(
            select(Publisher).where(Publisher.normalized_name == normalized_name)
        )
        return result.scalar_one_or_none()

    async def list_publishers(
        self,
        *,
        cursor: str | None,
        limit: int,
        query: str | None,
    ) -> tuple[list[Publisher], str | None]:
        statement = select(Publisher).order_by(Publisher.id.desc()).limit(limit + 1)
        if cursor:
            cursor_publisher = await self.get_publisher_by_public_id(cursor)
            if cursor_publisher is not None:
                statement = statement.where(Publisher.id < cursor_publisher.id)
        if query:
            statement = statement.where(Publisher.name.ilike(f"%{query.strip()}%"))
        result = await self.session.execute(statement)
        rows = list(result.scalars().all())
        next_cursor = rows[limit].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def get_publisher_by_public_id(self, public_id: str) -> Publisher | None:
        result = await self.session.execute(
            select(Publisher).where(Publisher.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_category_by_public_id_or_slug(self, value: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(or_(Category.public_id == value, Category.slug == value))
        )
        return result.scalar_one_or_none()

    async def list_categories(self, *, active_only: bool = True) -> list[Category]:
        statement = select(Category).order_by(Category.sort_order.asc(), Category.name.asc())
        if active_only:
            statement = statement.where(Category.is_active.is_(True))
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_or_create_author(self, name: str, normalized_name: str) -> Author:
        author = await self.get_author_by_normalized_name(normalized_name)
        if author is not None:
            return author
        author = Author(name=name, normalized_name=normalized_name)
        self.add(author)
        await self.flush()
        return author

    async def get_or_create_publisher(
        self,
        *,
        name: str,
        normalized_name: str,
        website_url: str | None,
    ) -> Publisher:
        publisher = await self.get_publisher_by_normalized_name(normalized_name)
        if publisher is not None:
            if website_url and publisher.website_url is None:
                publisher.website_url = website_url
            return publisher
        publisher = Publisher(
            name=name,
            normalized_name=normalized_name,
            website_url=website_url,
        )
        self.add(publisher)
        await self.flush()
        return publisher

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


def edition_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(BookEdition.academic_metadata),
        selectinload(BookEdition.identifiers),
        selectinload(BookEdition.publisher),
        selectinload(BookEdition.book).selectinload(Book.authors).selectinload(BookAuthor.author),
        selectinload(BookEdition.book)
        .selectinload(Book.categories)
        .selectinload(BookCategory.category),
    )


def apply_book_filters(
    statement: Select[tuple[BookEdition]],
    *,
    author: str | None,
    category: Category | None,
    identifier: tuple[str, str] | None,
    language: str | None,
    publisher: str | None,
    query: str | None,
) -> Select[tuple[BookEdition]]:
    if identifier:
        identifier_type, identifier_value = identifier
        statement = statement.where(
            select(BookIdentifier.id)
            .where(
                BookIdentifier.book_edition_id == BookEdition.id,
                BookIdentifier.identifier_type == identifier_type,
                BookIdentifier.identifier_value == identifier_value,
            )
            .exists()
        )
    if category is not None:
        statement = statement.where(
            select(BookCategory.id)
            .where(
                BookCategory.book_id == BookEdition.book_id,
                BookCategory.category_id == category.id,
            )
            .exists()
        )
    if language:
        statement = statement.where(BookEdition.language == language.strip().lower())
    if publisher:
        statement = statement.where(
            BookEdition.publisher.has(Publisher.name.ilike(f"%{publisher.strip()}%"))
        )
    if author:
        statement = statement.where(author_match_exists(author))
    if query:
        pattern = f"%{query.strip()}%"
        statement = statement.where(
            or_(
                BookEdition.title.ilike(pattern),
                BookEdition.subtitle.ilike(pattern),
                BookEdition.description.ilike(pattern),
                BookEdition.publisher.has(Publisher.name.ilike(pattern)),
                author_match_exists(query),
                select(BookIdentifier.id)
                .where(
                    BookIdentifier.book_edition_id == BookEdition.id,
                    BookIdentifier.identifier_value.ilike(pattern),
                )
                .exists(),
            )
        )
    return statement


def author_match_exists(value: str) -> ColumnElement[bool]:
    pattern = f"%{value.strip()}%"
    return (
        select(BookAuthor.id)
        .join(Author, BookAuthor.author_id == Author.id)
        .where(
            BookAuthor.book_id == BookEdition.book_id,
            Author.name.ilike(pattern),
        )
        .exists()
    )


__all__ = [
    "AcademicMetadata",
    "Author",
    "Book",
    "BookAuthor",
    "BookCategory",
    "BookEdition",
    "BookIdentifier",
    "CatalogRepository",
    "Category",
    "Publisher",
]
