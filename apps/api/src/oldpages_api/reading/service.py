from __future__ import annotations

import calendar
import re
from collections import Counter, defaultdict
from datetime import date
from typing import Any, cast
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.catalog.models import BookEdition
from oldpages_api.communities.permissions import require_active_member
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.reading.events import (
    READING_GOAL_CREATED,
    READING_NOTE_CREATED,
    READING_PROGRESS_UPDATED,
    READING_STATISTICS_RECOMPUTED,
    SHELF_CREATED,
    SHELF_ITEM_ADDED,
    SHELF_ITEM_REMOVED,
)
from oldpages_api.reading.exceptions import (
    ForbiddenReadingActionError,
    ReadingNotFoundError,
    ReadingValidationError,
)
from oldpages_api.reading.models import (
    ReadingGoal,
    ReadingNote,
    ReadingProgress,
    ReadingStatistic,
    Shelf,
    ShelfItem,
)
from oldpages_api.reading.repository import ReadingRepository
from oldpages_api.reading.schemas import (
    ReadingBookSummary,
    ReadingGoalCreateRequest,
    ReadingGoalListResponse,
    ReadingGoalResponse,
    ReadingGoalScope,
    ReadingGoalStatus,
    ReadingGoalType,
    ReadingNoteCreateRequest,
    ReadingNoteListResponse,
    ReadingNoteResponse,
    ReadingNoteType,
    ReadingNoteVisibility,
    ReadingProgressListResponse,
    ReadingProgressResponse,
    ReadingProgressUpdateRequest,
    ReadingStatisticListResponse,
    ReadingStatisticPeriod,
    ReadingStatisticRecomputeRequest,
    ReadingStatisticResponse,
    ReadingStatus,
    ShelfCreateRequest,
    ShelfItemCreateRequest,
    ShelfItemResponse,
    ShelfListResponse,
    ShelfResponse,
    ShelfType,
    ShelfVisibility,
)

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")

DEFAULT_SHELVES: tuple[tuple[str, str, str, int], ...] = (
    ("Want to read", "want-to-read", "want_to_read", 0),
    ("Currently reading", "currently-reading", "currently_reading", 1),
    ("Finished", "finished", "finished", 2),
    ("Did not finish", "did-not-finish", "did_not_finish", 3),
    ("Owned", "owned", "owned", 4),
    ("Previously owned", "previously-owned", "previously_owned", 5),
    ("Available for exchange", "available-for-exchange", "available_for_exchange", 6),
    ("Available for lending", "available-for-lending", "available_for_lending", 7),
    ("Favorites", "favorites", "favorites", 8),
    ("Academic books", "academic-books", "academic_books", 9),
    ("Rare collection", "rare-collection", "rare_collection", 10),
)

PROGRESS_STATUS_TO_SHELF = {
    "want_to_read": "want-to-read",
    "currently_reading": "currently-reading",
    "finished": "finished",
    "did_not_finish": "did-not-finish",
}


class ReadingService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ReadingRepository(session)

    async def create_shelf(
        self,
        payload: ShelfCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ShelfResponse:
        await self.ensure_default_shelves(actor)
        slug = slugify(payload.slug or payload.name)
        existing = await self.repo.get_shelf_by_slug(actor.id, slug)
        if existing is not None:
            raise ReadingValidationError("Shelf slug is already in use.")
        shelf = Shelf(
            is_system=False,
            name=payload.name,
            shelf_type="custom",
            slug=slug,
            sort_order=100,
            user_id=actor.id,
            visibility=payload.visibility,
        )
        self.repo.add(shelf)
        await self.repo.flush()
        await self.audit(
            action=SHELF_CREATED,
            actor=actor,
            context=context,
            payload={"shelf_id": shelf.public_id, "slug": shelf.slug},
        )
        await self.repo.commit()
        reloaded = await self.get_shelf_model(shelf.public_id)
        return shelf_response(reloaded, include_items=True)

    async def list_my_shelves(self, actor: User) -> ShelfListResponse:
        await self.ensure_default_shelves(actor)
        await self.repo.commit()
        shelves = await self.repo.list_shelves(actor.id)
        return ShelfListResponse(
            items=[shelf_response(shelf, include_items=True) for shelf in shelves]
        )

    async def list_public_shelves(self, user_id: str, viewer: User | None) -> ShelfListResponse:
        user = await self.repo.get_user_by_public_id(user_id)
        if user is None:
            raise ReadingNotFoundError("User was not found.")
        if user.profile.hide_shelves and (viewer is None or viewer.id != user.id):
            return ShelfListResponse(items=[])
        public_only = viewer is None or viewer.id != user.id
        shelves = await self.repo.list_shelves(user.id, public_only=public_only)
        return ShelfListResponse(
            items=[shelf_response(shelf, include_items=True) for shelf in shelves]
        )

    async def add_shelf_item(
        self,
        shelf_id: str,
        payload: ShelfItemCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ShelfItemResponse:
        shelf = await self.get_shelf_model(shelf_id)
        require_shelf_owner(shelf, actor)
        book = await self.get_book(payload.book_id)
        await self.add_book_to_shelf(
            shelf=shelf,
            book=book,
            actor=actor,
            note=payload.note,
            sort_order=payload.sort_order,
        )
        await self.audit(
            action=SHELF_ITEM_ADDED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id, "shelf_id": shelf.public_id},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_shelf_item(shelf.id, book.id)
        if reloaded is None:
            raise ReadingValidationError("Shelf item could not be created.")
        return shelf_item_response(reloaded)

    async def remove_shelf_item(
        self,
        shelf_id: str,
        book_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> None:
        shelf = await self.get_shelf_model(shelf_id)
        require_shelf_owner(shelf, actor)
        book = await self.get_book(book_id)
        await self.repo.delete_shelf_item(shelf.id, book.id)
        await self.audit(
            action=SHELF_ITEM_REMOVED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id, "shelf_id": shelf.public_id},
        )
        await self.repo.commit()

    async def update_progress(
        self,
        book_id: str,
        payload: ReadingProgressUpdateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReadingProgressResponse:
        book = await self.get_book(book_id)
        if payload.current_page is not None and book.page_count is not None:
            if payload.current_page > book.page_count:
                raise ReadingValidationError("current_page cannot exceed book page_count.")
        progress = await self.repo.get_progress(actor.id, book.id)
        if progress is None:
            progress = ReadingProgress(
                book_edition_id=book.id,
                daily_minutes_json={},
                status=payload.status,
                total_reading_minutes=0,
                user_id=actor.id,
            )
            self.repo.add(progress)
            await self.repo.flush()
        progress.status = payload.status
        progress.current_page = payload.current_page
        progress.percent_complete = percent_complete(payload, book)
        progress.started_on = payload.started_on or progress.started_on
        progress.finished_on = finish_date(payload)
        progress.last_progress_at = utc_now()
        progress.rating = payload.rating
        progress.review_text = payload.review_text
        if payload.reread_count is not None:
            progress.reread_count = payload.reread_count
        if payload.reading_minutes is not None:
            reading_day = payload.progressed_on or progress_date_for_actor(actor)
            daily_minutes = dict(progress.daily_minutes_json)
            daily_minutes[reading_day.isoformat()] = payload.reading_minutes
            progress.daily_minutes_json = daily_minutes
            progress.total_reading_minutes = sum(int(value) for value in daily_minutes.values())

        await self.ensure_default_shelves(actor)
        await self.add_progress_shelf_item(actor, book, payload.status)
        await self.audit(
            action=READING_PROGRESS_UPDATED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id, "status": progress.status},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_progress(actor.id, book.id)
        if reloaded is None:
            raise ReadingValidationError("Reading progress could not be saved.")
        return progress_response(reloaded)

    async def list_progress(self, actor: User) -> ReadingProgressListResponse:
        progress = await self.repo.list_progress(actor.id)
        return ReadingProgressListResponse(items=[progress_response(item) for item in progress])

    async def create_note(
        self,
        payload: ReadingNoteCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReadingNoteResponse:
        if payload.client_note_id:
            existing = await self.repo.get_note_by_client_id(actor.id, payload.client_note_id)
            if existing is not None:
                return note_response(existing)
        book = await self.get_book(payload.book_id)
        progress = await self.repo.get_progress(actor.id, book.id)
        note = ReadingNote(
            body=payload.body,
            book_edition_id=book.id,
            client_note_id=payload.client_note_id,
            note_type=payload.note_type,
            page_number=payload.page_number,
            percent_complete=payload.percent_complete,
            progress_id=progress.id if progress is not None else None,
            user_id=actor.id,
            visibility=payload.visibility,
        )
        self.repo.add(note)
        await self.repo.flush()
        await self.audit(
            action=READING_NOTE_CREATED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id, "note_id": note.public_id},
        )
        await self.repo.commit()
        reloaded = (
            await self.repo.get_note_by_client_id(actor.id, payload.client_note_id)
            if payload.client_note_id
            else None
        )
        if reloaded is not None:
            return note_response(reloaded)
        notes = await self.repo.list_notes(actor.id, book_edition_id=book.id)
        return note_response(next(item for item in notes if item.public_id == note.public_id))

    async def list_notes(
        self,
        actor: User,
        *,
        book_id: str | None,
    ) -> ReadingNoteListResponse:
        book_edition_id = None
        if book_id:
            book = await self.get_book(book_id)
            book_edition_id = book.id
        notes = await self.repo.list_notes(actor.id, book_edition_id=book_edition_id)
        return ReadingNoteListResponse(items=[note_response(note) for note in notes])

    async def list_public_notes(self, user_id: str, book_id: str | None) -> ReadingNoteListResponse:
        user = await self.repo.get_user_by_public_id(user_id)
        if user is None:
            raise ReadingNotFoundError("User was not found.")
        book_edition_id = None
        if book_id:
            book = await self.get_book(book_id)
            book_edition_id = book.id
        notes = await self.repo.list_notes(
            user.id,
            book_edition_id=book_edition_id,
            public_only=True,
        )
        return ReadingNoteListResponse(items=[note_response(note) for note in notes])

    async def create_goal(
        self,
        payload: ReadingGoalCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReadingGoalResponse:
        community_id = None
        target_metadata = dict(payload.target_metadata)
        if payload.scope == "community":
            community = await self.repo.get_community_by_public_id(
                cast("str", payload.community_id)
            )
            if community is None:
                raise ReadingValidationError("Community was not found.")
            require_active_member(actor, community)
            community_id = community.id
        if payload.scope == "institution":
            actor_with_profile = await self.repo.get_user_by_public_id(actor.public_id)
            if actor_with_profile is None:
                raise ReadingValidationError("User was not found.")
            actor_institution = actor_with_profile.profile.institution
            institution = str(target_metadata.get("institution") or actor_institution or "")
            if not actor_institution or actor_institution != institution:
                raise ForbiddenReadingActionError(
                    "Institution goals require matching profile institution."
                )
            target_metadata["institution"] = institution
        goal = ReadingGoal(
            community_id=community_id,
            goal_type=payload.goal_type,
            period_end=payload.period_end,
            period_start=payload.period_start,
            scope=payload.scope,
            target_metadata_json=target_metadata,
            target_value=payload.target_value,
            timezone=payload.timezone,
            user_id=actor.id,
        )
        self.repo.add(goal)
        await self.repo.flush()
        await self.audit(
            action=READING_GOAL_CREATED,
            actor=actor,
            context=context,
            payload={
                "goal_id": goal.public_id,
                "goal_type": goal.goal_type,
                "scope": goal.scope,
            },
        )
        await self.repo.commit()
        reloaded = await self.repo.get_goal_by_public_id(goal.public_id)
        if reloaded is None:
            raise ReadingValidationError("Reading goal could not be created.")
        return goal_response(reloaded)

    async def list_goals(self, actor: User) -> ReadingGoalListResponse:
        goals = await self.repo.list_goals(actor.id)
        return ReadingGoalListResponse(items=[goal_response(goal) for goal in goals])

    async def recompute_statistics(
        self,
        payload: ReadingStatisticRecomputeRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReadingStatisticResponse:
        period_start, period_end = statistic_period(payload)
        progresses = await self.repo.list_all_progress_for_statistics(actor.id)
        computed = compute_statistics(
            progresses,
            period_type=payload.period_type,
            period_start=period_start,
            period_end=period_end,
            timezone=payload.timezone,
        )
        statistic = await self.repo.get_statistic(
            user_id=actor.id,
            period_type=payload.period_type,
            period_start=period_start,
            timezone=payload.timezone,
        )
        if statistic is None:
            statistic = ReadingStatistic(
                period_end=period_end,
                period_start=period_start,
                period_type=payload.period_type,
                timezone=payload.timezone,
                user_id=actor.id,
                **computed,
            )
            self.repo.add(statistic)
        else:
            statistic.period_end = period_end
            statistic.books_completed = computed["books_completed"]
            statistic.pages_read = computed["pages_read"]
            statistic.minutes_read = computed["minutes_read"]
            statistic.reading_streak_days = computed["reading_streak_days"]
            statistic.genres_json = computed["genres_json"]
            statistic.authors_json = computed["authors_json"]
            statistic.monthly_progress_json = computed["monthly_progress_json"]
            statistic.year_summary_json = computed["year_summary_json"]
            statistic.computed_at = computed["computed_at"]
        await self.repo.flush()
        await self.audit(
            action=READING_STATISTICS_RECOMPUTED,
            actor=actor,
            context=context,
            payload={
                "period_start": period_start.isoformat(),
                "period_type": payload.period_type,
                "timezone": payload.timezone,
            },
        )
        await self.repo.commit()
        return statistic_response(statistic)

    async def list_statistics(self, actor: User) -> ReadingStatisticListResponse:
        statistics = await self.repo.list_statistics(actor.id)
        return ReadingStatisticListResponse(
            items=[statistic_response(statistic) for statistic in statistics]
        )

    async def ensure_default_shelves(self, actor: User) -> None:
        for name, slug, shelf_type, sort_order in DEFAULT_SHELVES:
            existing = await self.repo.get_shelf_by_slug(actor.id, slug)
            if existing is None:
                self.repo.add(
                    Shelf(
                        is_system=True,
                        name=name,
                        shelf_type=shelf_type,
                        slug=slug,
                        sort_order=sort_order,
                        user_id=actor.id,
                        visibility="public"
                        if shelf_type in {"want_to_read", "finished"}
                        else "private",
                    )
                )
        await self.repo.flush()

    async def add_progress_shelf_item(
        self,
        actor: User,
        book: BookEdition,
        status_value: str,
    ) -> None:
        shelf_slug = PROGRESS_STATUS_TO_SHELF[status_value]
        shelf = await self.repo.get_shelf_by_slug(actor.id, shelf_slug)
        if shelf is None:
            raise ReadingValidationError("Default shelf was not created.")
        await self.add_book_to_shelf(
            shelf=shelf,
            book=book,
            actor=actor,
            note=None,
            sort_order=0,
        )

    async def add_book_to_shelf(
        self,
        *,
        shelf: Shelf,
        book: BookEdition,
        actor: User,
        note: str | None,
        sort_order: int,
    ) -> ShelfItem:
        item = await self.repo.get_shelf_item(shelf.id, book.id)
        if item is not None:
            if note is not None:
                item.note = note
            item.sort_order = sort_order
            return item
        item = ShelfItem(
            added_at=utc_now(),
            book_edition_id=book.id,
            note=note,
            shelf_id=shelf.id,
            sort_order=sort_order,
            user_id=actor.id,
        )
        self.repo.add(item)
        await self.repo.flush()
        return item

    async def get_shelf_model(self, shelf_id: str) -> Shelf:
        shelf = await self.repo.get_shelf_by_public_id(shelf_id)
        if shelf is None:
            raise ReadingNotFoundError("Shelf was not found.")
        return shelf

    async def get_book(self, book_id: str) -> BookEdition:
        book = await self.repo.get_book_edition_by_public_id(book_id)
        if book is None:
            raise ReadingValidationError("Book was not found.")
        return book

    async def audit(
        self,
        *,
        action: str,
        actor: User,
        context: AuthenticatedRequestContext,
        payload: dict[str, Any],
    ) -> None:
        self.repo.add(
            AuditLog(
                action=action,
                actor_user_id=actor.id,
                context_json=payload,
                ip_address=context.ip_address,
                target_user_id=None,
                user_agent=context.user_agent,
            )
        )


def require_shelf_owner(shelf: Shelf, actor: User) -> None:
    if shelf.user_id != actor.id:
        raise ForbiddenReadingActionError("Only the shelf owner can modify this shelf.")


def percent_complete(payload: ReadingProgressUpdateRequest, book: BookEdition) -> int | None:
    if payload.status == "finished":
        return 100
    if payload.percent_complete is not None:
        return payload.percent_complete
    if payload.current_page is not None and book.page_count:
        return min(100, int((payload.current_page / book.page_count) * 100))
    return None


def finish_date(payload: ReadingProgressUpdateRequest) -> date | None:
    if payload.status == "finished":
        return payload.finished_on or date.today()
    return payload.finished_on


def progress_date_for_actor(actor: User) -> date:
    del actor
    timezone = ZoneInfo("UTC")
    return utc_now().astimezone(timezone).date()


def statistic_period(payload: ReadingStatisticRecomputeRequest) -> tuple[date, date]:
    today = date.today()
    if payload.period_type == "all_time":
        return date(1970, 1, 1), date(9999, 12, 31)
    if payload.period_type == "year":
        start = payload.period_start or date(today.year, 1, 1)
        return date(start.year, 1, 1), date(start.year, 12, 31)
    start = payload.period_start or date(today.year, today.month, 1)
    last_day = calendar.monthrange(start.year, start.month)[1]
    return date(start.year, start.month, 1), date(start.year, start.month, last_day)


def compute_statistics(
    progresses: list[ReadingProgress],
    *,
    period_type: str,
    period_start: date,
    period_end: date,
    timezone: str,
) -> dict[str, Any]:
    completed = [
        item
        for item in progresses
        if item.status == "finished"
        and item.finished_on is not None
        and period_start <= item.finished_on <= period_end
    ]
    daily_minutes = merged_daily_minutes(progresses, period_start, period_end)
    books_completed = len(completed)
    pages_read = sum(book_page_count(item.book_edition) for item in completed)
    minutes_read = sum(daily_minutes.values())
    genres = Counter[str]()
    authors = Counter[str]()
    for item in completed:
        genres.update(item.book_edition.genres)
        authors.update(book_author_names(item.book_edition))
    monthly_progress = monthly_progress_summary(completed, daily_minutes)
    return {
        "authors_json": dict(authors),
        "books_completed": books_completed,
        "computed_at": utc_now(),
        "genres_json": dict(genres),
        "minutes_read": minutes_read,
        "monthly_progress_json": monthly_progress,
        "pages_read": pages_read,
        "reading_streak_days": longest_streak(daily_minutes),
        "year_summary_json": {
            "books_completed": books_completed,
            "pages_read": pages_read,
            "period_type": period_type,
            "timezone": timezone,
        },
    }


def merged_daily_minutes(
    progresses: list[ReadingProgress],
    period_start: date,
    period_end: date,
) -> dict[date, int]:
    merged: dict[date, int] = defaultdict(int)
    for progress in progresses:
        for day_text, minutes in progress.daily_minutes_json.items():
            day = date.fromisoformat(day_text)
            if period_start <= day <= period_end:
                merged[day] += int(minutes)
    return dict(merged)


def monthly_progress_summary(
    completed: list[ReadingProgress],
    daily_minutes: dict[date, int],
) -> dict[str, Any]:
    summary: dict[str, dict[str, int]] = defaultdict(
        lambda: {"books_completed": 0, "minutes_read": 0, "pages_read": 0}
    )
    for item in completed:
        if item.finished_on is None:
            continue
        bucket = item.finished_on.strftime("%Y-%m")
        summary[bucket]["books_completed"] += 1
        summary[bucket]["pages_read"] += book_page_count(item.book_edition)
    for day, minutes in daily_minutes.items():
        summary[day.strftime("%Y-%m")]["minutes_read"] += minutes
    return dict(summary)


def longest_streak(daily_minutes: dict[date, int]) -> int:
    days = sorted(day for day, minutes in daily_minutes.items() if minutes > 0)
    longest = 0
    current = 0
    previous: date | None = None
    for day in days:
        if previous is None or (day - previous).days == 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
        previous = day
    return longest


def book_page_count(book: BookEdition) -> int:
    return int(book.page_count or 0)


def book_author_names(book: BookEdition) -> list[str]:
    return [
        book_author.author.name
        for book_author in sorted(book.book.authors, key=lambda item: item.position)
    ]


def book_summary(book: BookEdition) -> ReadingBookSummary:
    return ReadingBookSummary(
        authors=book_author_names(book),
        genres=book.genres,
        id=book.public_id,
        page_count=book.page_count,
        title=book.title,
    )


def shelf_response(shelf: Shelf, *, include_items: bool) -> ShelfResponse:
    return ShelfResponse(
        id=shelf.public_id,
        is_system=shelf.is_system,
        items=[shelf_item_response(item) for item in shelf.items] if include_items else [],
        name=shelf.name,
        shelf_type=cast("ShelfType", shelf.shelf_type),
        slug=shelf.slug,
        sort_order=shelf.sort_order,
        visibility=cast("ShelfVisibility", shelf.visibility),
    )


def shelf_item_response(item: ShelfItem) -> ShelfItemResponse:
    return ShelfItemResponse(
        added_at=item.added_at,
        book=book_summary(item.book_edition),
        id=item.public_id,
        note=item.note,
        sort_order=item.sort_order,
    )


def progress_response(progress: ReadingProgress) -> ReadingProgressResponse:
    return ReadingProgressResponse(
        book=book_summary(progress.book_edition),
        current_page=progress.current_page,
        daily_minutes=progress.daily_minutes_json,
        finished_on=progress.finished_on,
        id=progress.public_id,
        last_progress_at=progress.last_progress_at,
        percent_complete=progress.percent_complete,
        rating=progress.rating,
        reread_count=progress.reread_count,
        review_text=progress.review_text,
        started_on=progress.started_on,
        status=cast("ReadingStatus", progress.status),
        total_reading_minutes=progress.total_reading_minutes,
    )


def note_response(note: ReadingNote) -> ReadingNoteResponse:
    return ReadingNoteResponse(
        body=note.body,
        book=book_summary(note.book_edition),
        created_at=note.created_at,
        id=note.public_id,
        note_type=cast("ReadingNoteType", note.note_type),
        page_number=note.page_number,
        percent_complete=note.percent_complete,
        visibility=cast("ReadingNoteVisibility", note.visibility),
    )


def goal_response(goal: ReadingGoal) -> ReadingGoalResponse:
    return ReadingGoalResponse(
        community_id=goal.community.public_id if goal.community else None,
        current_value=goal.current_value,
        goal_type=cast("ReadingGoalType", goal.goal_type),
        id=goal.public_id,
        period_end=goal.period_end,
        period_start=goal.period_start,
        scope=cast("ReadingGoalScope", goal.scope),
        status=cast("ReadingGoalStatus", goal.status),
        target_metadata=goal.target_metadata_json,
        target_value=goal.target_value,
        timezone=goal.timezone,
    )


def statistic_response(statistic: ReadingStatistic) -> ReadingStatisticResponse:
    return ReadingStatisticResponse(
        authors=statistic.authors_json,
        books_completed=statistic.books_completed,
        computed_at=statistic.computed_at,
        genres=statistic.genres_json,
        id=statistic.public_id,
        minutes_read=statistic.minutes_read,
        monthly_progress=statistic.monthly_progress_json,
        pages_read=statistic.pages_read,
        period_end=statistic.period_end,
        period_start=statistic.period_start,
        period_type=cast("ReadingStatisticPeriod", statistic.period_type),
        reading_streak_days=statistic.reading_streak_days,
        timezone=statistic.timezone,
        year_summary=statistic.year_summary_json,
    )


def slugify(value: str) -> str:
    slug = _SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
    if not slug:
        raise ReadingValidationError("Slug cannot be empty.")
    return slug[:140]
