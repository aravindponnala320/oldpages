from __future__ import annotations

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.catalog.models import Book, BookAuthor, BookEdition
from oldpages_api.communities.models import Community, CommunityMember
from oldpages_api.identity.models import User
from oldpages_api.reading.models import (
    ReadingGoal,
    ReadingNote,
    ReadingProgress,
    ReadingStatistic,
    Shelf,
    ShelfItem,
)


class ReadingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_book_edition_by_public_id(self, public_id: str) -> BookEdition | None:
        result = await self.session.execute(
            select(BookEdition)
            .options(*book_load_options())
            .where(BookEdition.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        result = await self.session.execute(
            select(User).options(selectinload(User.profile)).where(User.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_community_by_public_id(self, public_id: str) -> Community | None:
        result = await self.session.execute(
            select(Community)
            .options(
                selectinload(Community.members).selectinload(CommunityMember.role),
                selectinload(Community.owner),
            )
            .where(Community.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_shelf_by_public_id(self, public_id: str) -> Shelf | None:
        result = await self.session.execute(
            select(Shelf).options(*shelf_load_options()).where(Shelf.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_shelf_by_slug(self, user_id: int, slug: str) -> Shelf | None:
        result = await self.session.execute(
            select(Shelf)
            .options(*shelf_load_options())
            .where(Shelf.user_id == user_id, Shelf.slug == slug)
        )
        return result.unique().scalar_one_or_none()

    async def list_shelves(self, user_id: int, *, public_only: bool = False) -> list[Shelf]:
        stmt = (
            select(Shelf)
            .options(*shelf_load_options())
            .where(Shelf.user_id == user_id)
            .order_by(Shelf.sort_order.asc(), Shelf.id.asc())
        )
        if public_only:
            stmt = stmt.where(Shelf.visibility == "public")
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_shelf_item(self, shelf_id: int, book_edition_id: int) -> ShelfItem | None:
        result = await self.session.execute(
            select(ShelfItem)
            .options(*shelf_item_load_options())
            .where(ShelfItem.shelf_id == shelf_id, ShelfItem.book_edition_id == book_edition_id)
        )
        return result.unique().scalar_one_or_none()

    async def delete_shelf_item(self, shelf_id: int, book_edition_id: int) -> None:
        await self.session.execute(
            delete(ShelfItem).where(
                ShelfItem.shelf_id == shelf_id,
                ShelfItem.book_edition_id == book_edition_id,
            )
        )

    async def get_progress(self, user_id: int, book_edition_id: int) -> ReadingProgress | None:
        result = await self.session.execute(
            select(ReadingProgress)
            .options(*progress_load_options())
            .where(
                ReadingProgress.user_id == user_id,
                ReadingProgress.book_edition_id == book_edition_id,
            )
        )
        return result.unique().scalar_one_or_none()

    async def list_progress(self, user_id: int) -> list[ReadingProgress]:
        result = await self.session.execute(
            select(ReadingProgress)
            .options(*progress_load_options())
            .where(ReadingProgress.user_id == user_id)
            .order_by(ReadingProgress.updated_at.desc(), ReadingProgress.id.desc())
        )
        return list(result.unique().scalars().all())

    async def get_note_by_client_id(
        self,
        user_id: int,
        client_note_id: str,
    ) -> ReadingNote | None:
        result = await self.session.execute(
            select(ReadingNote)
            .options(*note_load_options())
            .where(
                ReadingNote.user_id == user_id,
                ReadingNote.client_note_id == client_note_id,
            )
        )
        return result.unique().scalar_one_or_none()

    async def list_notes(
        self,
        user_id: int,
        *,
        book_edition_id: int | None = None,
        public_only: bool = False,
    ) -> list[ReadingNote]:
        stmt = (
            select(ReadingNote)
            .options(*note_load_options())
            .where(ReadingNote.user_id == user_id)
            .order_by(ReadingNote.created_at.desc(), ReadingNote.id.desc())
        )
        if book_edition_id is not None:
            stmt = stmt.where(ReadingNote.book_edition_id == book_edition_id)
        if public_only:
            stmt = stmt.where(ReadingNote.visibility == "public")
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_goals(self, user_id: int) -> list[ReadingGoal]:
        result = await self.session.execute(
            select(ReadingGoal)
            .options(selectinload(ReadingGoal.community))
            .where(ReadingGoal.user_id == user_id)
            .order_by(ReadingGoal.period_start.desc(), ReadingGoal.id.desc())
        )
        return list(result.unique().scalars().all())

    async def get_goal_by_public_id(self, public_id: str) -> ReadingGoal | None:
        result = await self.session.execute(
            select(ReadingGoal)
            .options(selectinload(ReadingGoal.community))
            .where(ReadingGoal.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_all_progress_for_statistics(self, user_id: int) -> list[ReadingProgress]:
        result = await self.session.execute(
            select(ReadingProgress)
            .options(*progress_load_options())
            .where(ReadingProgress.user_id == user_id)
        )
        return list(result.unique().scalars().all())

    async def get_statistic(
        self,
        *,
        user_id: int,
        period_type: str,
        period_start: date,
        timezone: str,
    ) -> ReadingStatistic | None:
        result = await self.session.execute(
            select(ReadingStatistic).where(
                ReadingStatistic.user_id == user_id,
                ReadingStatistic.period_type == period_type,
                ReadingStatistic.period_start == period_start,
                ReadingStatistic.timezone == timezone,
            )
        )
        return result.scalar_one_or_none()

    async def list_statistics(self, user_id: int) -> list[ReadingStatistic]:
        result = await self.session.execute(
            select(ReadingStatistic)
            .where(ReadingStatistic.user_id == user_id)
            .order_by(ReadingStatistic.period_start.desc(), ReadingStatistic.id.desc())
        )
        return list(result.scalars().all())

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def book_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(BookEdition.book).selectinload(Book.authors).selectinload(BookAuthor.author),
    )


def shelf_item_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(ShelfItem.book_edition)
        .selectinload(BookEdition.book)
        .selectinload(Book.authors)
        .selectinload(BookAuthor.author),
    )


def shelf_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Shelf.items)
        .selectinload(ShelfItem.book_edition)
        .selectinload(BookEdition.book)
        .selectinload(Book.authors)
        .selectinload(BookAuthor.author),
    )


def progress_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(ReadingProgress.book_edition)
        .selectinload(BookEdition.book)
        .selectinload(Book.authors)
        .selectinload(BookAuthor.author),
    )


def note_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(ReadingNote.book_edition)
        .selectinload(BookEdition.book)
        .selectinload(Book.authors)
        .selectinload(BookAuthor.author),
    )


__all__ = ["ReadingRepository"]
