from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.business.models import (
    BusinessLocation,
    BusinessProfile,
    InventoryImport,
    StaffAccount,
)


class BusinessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_profile_by_id(self, profile_id: int) -> BusinessProfile | None:
        result = await self.session.execute(
            select(BusinessProfile)
            .execution_options(populate_existing=True)
            .options(*profile_load_options())
            .where(BusinessProfile.id == profile_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_profile_by_public_id(self, public_id: str) -> BusinessProfile | None:
        result = await self.session.execute(
            select(BusinessProfile)
            .execution_options(populate_existing=True)
            .options(*profile_load_options())
            .where(BusinessProfile.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_profile_by_slug(self, slug: str) -> BusinessProfile | None:
        result = await self.session.execute(
            select(BusinessProfile)
            .execution_options(populate_existing=True)
            .options(*profile_load_options())
            .where(BusinessProfile.slug == slug)
        )
        return result.unique().scalar_one_or_none()

    async def get_profile_by_owner(self, user_id: int) -> BusinessProfile | None:
        result = await self.session.execute(
            select(BusinessProfile)
            .execution_options(populate_existing=True)
            .options(*profile_load_options())
            .where(BusinessProfile.owner_user_id == user_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_profiles(
        self,
        filters: dict[str, str] | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[BusinessProfile]:
        status_filter = (filters or {}).get("status", "active") or "active"
        query = (
            select(BusinessProfile)
            .options(*profile_load_options())
            .where(BusinessProfile.status == status_filter)
            .order_by(BusinessProfile.id.desc())
            .limit(limit)
        )
        if cursor is not None:
            query = query.where(BusinessProfile.public_id < cursor)
        if filters:
            if "type" in filters:
                query = query.where(BusinessProfile.type == filters["type"])
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def get_location(self, location_id: int) -> BusinessLocation | None:
        result = await self.session.execute(
            select(BusinessLocation).where(BusinessLocation.id == location_id)
        )
        return result.scalar_one_or_none()

    async def get_location_by_public_id(self, public_id: str) -> BusinessLocation | None:
        result = await self.session.execute(
            select(BusinessLocation).where(BusinessLocation.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def list_locations(self, business_id: int) -> list[BusinessLocation]:
        result = await self.session.execute(
            select(BusinessLocation)
            .where(BusinessLocation.business_profile_id == business_id)
            .order_by(BusinessLocation.is_primary.desc(), BusinessLocation.id.asc())
        )
        return list(result.scalars().all())

    async def get_staff(self, business_id: int, user_id: int) -> StaffAccount | None:
        result = await self.session.execute(
            select(StaffAccount).where(
                StaffAccount.business_profile_id == business_id,
                StaffAccount.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_staff_by_public_id(self, public_id: str) -> StaffAccount | None:
        result = await self.session.execute(
            select(StaffAccount).where(StaffAccount.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def list_staff(self, business_id: int) -> list[StaffAccount]:
        result = await self.session.execute(
            select(StaffAccount)
            .options(selectinload(StaffAccount.user))
            .where(StaffAccount.business_profile_id == business_id)
            .order_by(StaffAccount.id.asc())
        )
        return list(result.scalars().all())

    async def get_import(self, import_id: int) -> InventoryImport | None:
        result = await self.session.execute(
            select(InventoryImport).where(InventoryImport.id == import_id)
        )
        return result.scalar_one_or_none()

    async def get_import_by_public_id(self, public_id: str) -> InventoryImport | None:
        result = await self.session.execute(
            select(InventoryImport)
            .options(selectinload(InventoryImport.business_profile))
            .where(InventoryImport.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_import_by_payload_hash(
        self,
        business_id: int,
        payload_hash: str,
    ) -> InventoryImport | None:
        result = await self.session.execute(
            select(InventoryImport)
            .options(selectinload(InventoryImport.business_profile))
            .where(
                InventoryImport.business_profile_id == business_id,
                InventoryImport.payload_hash == payload_hash,
            )
        )
        return result.scalar_one_or_none()

    async def list_imports(
        self,
        business_id: int,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[InventoryImport]:
        query = (
            select(InventoryImport)
            .where(InventoryImport.business_profile_id == business_id)
            .order_by(InventoryImport.id.desc())
            .limit(limit)
        )
        if cursor is not None:
            query = query.where(InventoryImport.public_id < cursor)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def profile_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(BusinessProfile.owner),
        selectinload(BusinessProfile.locations),
        selectinload(BusinessProfile.staff_accounts).selectinload(StaffAccount.user),
    )


__all__ = ["BusinessRepository"]
