from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.chat.models import Conversation, Message
from oldpages_api.commerce.models import Review
from oldpages_api.identity.models import User, UserPreference
from oldpages_api.listings.models import Listing
from oldpages_api.trust.models import (
    CopyrightClaim,
    DeviceRisk,
    ModerationAction,
    ModerationCase,
    Report,
    RiskEvent,
)


class TrustRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_listing_by_public_id(self, public_id: str) -> Listing | None:
        result = await self.session.execute(
            select(Listing)
            .options(selectinload(Listing.seller))
            .where(Listing.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_message_by_public_id(self, public_id: str) -> Message | None:
        result = await self.session.execute(
            select(Message)
            .options(
                selectinload(Message.conversation)
                .selectinload(Conversation.messages)
                .selectinload(Message.sender),
                selectinload(Message.sender),
            )
            .where(Message.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_review_by_public_id(self, public_id: str) -> Review | None:
        result = await self.session.execute(select(Review).where(Review.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_report_by_public_id(self, public_id: str) -> Report | None:
        result = await self.session.execute(
            select(Report)
            .execution_options(populate_existing=True)
            .options(*report_load_options())
            .where(Report.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_report_by_id(self, report_id: int) -> Report | None:
        result = await self.session.execute(
            select(Report)
            .execution_options(populate_existing=True)
            .options(*report_load_options())
            .where(Report.id == report_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_case_by_public_id(self, public_id: str) -> ModerationCase | None:
        result = await self.session.execute(
            select(ModerationCase)
            .execution_options(populate_existing=True)
            .options(*case_load_options())
            .where(ModerationCase.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_cases(
        self,
        *,
        cursor: str | None,
        limit: int,
        status: str | None,
    ) -> tuple[list[ModerationCase], str | None]:
        stmt = (
            select(ModerationCase)
            .options(*case_load_options())
            .order_by(
                ModerationCase.priority_score.desc(),
                ModerationCase.created_at.asc(),
                ModerationCase.id.asc(),
            )
            .limit(limit + 1)
        )
        if status:
            stmt = stmt.where(ModerationCase.status == status)
        if cursor:
            cursor_case = await self.get_case_by_public_id(cursor)
            if cursor_case is not None:
                stmt = stmt.where(ModerationCase.id > cursor_case.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def report_count_for_user(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Report.id)).where(Report.target_user_id == user_id)
        )
        return int(result.scalar_one())

    async def report_count_for_listing(self, listing_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Report.id)).where(Report.target_listing_id == listing_id)
        )
        return int(result.scalar_one())

    async def get_device_risk_by_fingerprint(self, fingerprint: str) -> DeviceRisk | None:
        result = await self.session.execute(
            select(DeviceRisk).where(DeviceRisk.device_fingerprint == fingerprint)
        )
        return result.scalar_one_or_none()

    async def user_has_role(self, user_id: int, role: str) -> bool:
        result = await self.session.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preference = result.scalar_one_or_none()
        if preference is None:
            return False
        roles = preference.metadata_json.get("roles", [])
        return isinstance(roles, list) and role in roles

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def report_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Report.case),
        selectinload(Report.reporter),
        selectinload(Report.target_listing).selectinload(Listing.seller),
        selectinload(Report.target_message).selectinload(Message.conversation),
        selectinload(Report.target_message).selectinload(Message.sender),
        selectinload(Report.target_review),
        selectinload(Report.target_user),
    )


def case_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(ModerationCase.actions).selectinload(ModerationAction.actor),
        selectinload(ModerationCase.actions).selectinload(ModerationAction.moderator),
        selectinload(ModerationCase.assigned_moderator),
        selectinload(ModerationCase.report).selectinload(Report.case),
        selectinload(ModerationCase.report).selectinload(Report.reporter),
        selectinload(ModerationCase.report)
        .selectinload(Report.target_listing)
        .selectinload(Listing.seller),
        selectinload(ModerationCase.report)
        .selectinload(Report.target_message)
        .selectinload(Message.sender),
        selectinload(ModerationCase.report).selectinload(Report.target_review),
        selectinload(ModerationCase.report).selectinload(Report.target_user),
    )


__all__ = [
    "CopyrightClaim",
    "DeviceRisk",
    "ModerationAction",
    "ModerationCase",
    "Report",
    "RiskEvent",
    "TrustRepository",
]
