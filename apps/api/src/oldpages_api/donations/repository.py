from __future__ import annotations

from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.donations.models import (
    DonationCampaign,
    DonationNeed,
    DonationPledge,
    DonationReceipt,
)


class DonationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_campaign_by_id(self, campaign_id: int) -> DonationCampaign | None:
        result = await self.session.execute(
            select(DonationCampaign)
            .execution_options(populate_existing=True)
            .options(*campaign_load_options())
            .where(DonationCampaign.id == campaign_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_campaign_by_public_id(self, public_id: str) -> DonationCampaign | None:
        result = await self.session.execute(
            select(DonationCampaign)
            .execution_options(populate_existing=True)
            .options(*campaign_load_options())
            .where(DonationCampaign.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_campaigns(
        self,
        filters: dict[str, str | None],
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[DonationCampaign]:
        stmt = (
            select(DonationCampaign)
            .options(*campaign_load_options())
            .where(DonationCampaign.is_public.is_(True))
            .where(DonationCampaign.status == "active")
            .order_by(DonationCampaign.id.desc())
            .limit(limit)
        )
        if filters.get("city"):
            stmt = stmt.where(DonationCampaign.city == filters["city"])
        if filters.get("state"):
            stmt = stmt.where(DonationCampaign.state == filters["state"])
        if filters.get("institution_id"):
            from oldpages_api.institutions.models import Institution

            result_id = await self.session.execute(
                select(Institution.id).where(Institution.public_id == filters["institution_id"])
            )
            inst_id = result_id.scalar_one_or_none()
            if inst_id:
                stmt = stmt.where(DonationCampaign.institution_id == inst_id)
        if cursor:
            result = await self.session.execute(
                select(DonationCampaign.id).where(DonationCampaign.public_id == cursor)
            )
            cursor_id = result.scalar_one_or_none()
            if cursor_id is not None:
                stmt = stmt.where(DonationCampaign.id < cursor_id)
        result = await self.session.execute(stmt)
        return cast("list[DonationCampaign]", result.unique().scalars().all())

    async def get_pledge_by_public_id(self, public_id: str) -> DonationPledge | None:
        result = await self.session.execute(
            select(DonationPledge)
            .execution_options(populate_existing=True)
            .options(*pledge_load_options())
            .where(DonationPledge.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_pledges(
        self,
        campaign_id: int,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[DonationPledge]:
        stmt = (
            select(DonationPledge)
            .options(*pledge_load_options())
            .where(DonationPledge.campaign_id == campaign_id)
            .order_by(DonationPledge.id.desc())
            .limit(limit)
        )
        if cursor:
            result = await self.session.execute(
                select(DonationPledge.id).where(DonationPledge.public_id == cursor)
            )
            cursor_id = result.scalar_one_or_none()
            if cursor_id is not None:
                stmt = stmt.where(DonationPledge.id < cursor_id)
        result = await self.session.execute(stmt)
        return cast("list[DonationPledge]", result.unique().scalars().all())

    async def list_my_pledges(
        self,
        donor_user_id: int,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[DonationPledge]:
        stmt = (
            select(DonationPledge)
            .options(*pledge_load_options())
            .where(DonationPledge.donor_user_id == donor_user_id)
            .order_by(DonationPledge.id.desc())
            .limit(limit)
        )
        if cursor:
            result = await self.session.execute(
                select(DonationPledge.id).where(DonationPledge.public_id == cursor)
            )
            cursor_id = result.scalar_one_or_none()
            if cursor_id is not None:
                stmt = stmt.where(DonationPledge.id < cursor_id)
        result = await self.session.execute(stmt)
        return cast("list[DonationPledge]", result.unique().scalars().all())

    async def get_need_by_public_id(self, public_id: str) -> DonationNeed | None:
        result = await self.session.execute(
            select(DonationNeed).where(DonationNeed.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_receipt_by_pledge_id(self, pledge_id: int) -> DonationReceipt | None:
        result = await self.session.execute(
            select(DonationReceipt)
            .options(selectinload(DonationReceipt.issued_by))
            .where(DonationReceipt.pledge_id == pledge_id)
        )
        return result.unique().scalar_one_or_none()

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def campaign_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(DonationCampaign.created_by),
        selectinload(DonationCampaign.needs),
        selectinload(DonationCampaign.pledges).selectinload(DonationPledge.donor),
        selectinload(DonationCampaign.pledges)
        .selectinload(DonationPledge.receipt)
        .selectinload(DonationReceipt.issued_by),
    )


def pledge_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(DonationPledge.campaign),
        selectinload(DonationPledge.donor),
        selectinload(DonationPledge.donation_need),
        selectinload(DonationPledge.receipt).selectinload(DonationReceipt.issued_by),
    )


__all__ = ["DonationRepository"]
