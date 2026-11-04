from __future__ import annotations

from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.institutions.models import Institution, InstitutionDomain, InstitutionMember


class InstitutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_institution_by_id(self, institution_id: int) -> Institution | None:
        result = await self.session.execute(
            select(Institution)
            .execution_options(populate_existing=True)
            .options(*institution_load_options())
            .where(Institution.id == institution_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_institution_by_public_id(self, public_id: str) -> Institution | None:
        result = await self.session.execute(
            select(Institution)
            .execution_options(populate_existing=True)
            .options(*institution_load_options())
            .where(Institution.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_institution_by_slug(self, slug: str) -> Institution | None:
        result = await self.session.execute(
            select(Institution)
            .execution_options(populate_existing=True)
            .options(*institution_load_options())
            .where(Institution.slug == slug)
        )
        return result.unique().scalar_one_or_none()

    async def get_institution_by_owner(self, user_id: int) -> Institution | None:
        result = await self.session.execute(
            select(Institution)
            .options(*institution_load_options())
            .where(
                Institution.owner_user_id == user_id,
                Institution.status.in_(["pending", "active", "suspended"]),
            )
        )
        return result.unique().scalar_one_or_none()

    async def list_institutions(
        self,
        filters: dict[str, str | None],
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[Institution]:
        status_filter = filters.get("status", "active") or "active"
        stmt = (
            select(Institution)
            .options(*institution_load_options())
            .where(Institution.status == status_filter)
            .order_by(Institution.id.desc())
            .limit(limit)
        )
        if filters.get("type"):
            stmt = stmt.where(Institution.type == filters["type"])
        if filters.get("city"):
            stmt = stmt.where(Institution.city == filters["city"])
        if filters.get("state"):
            stmt = stmt.where(Institution.state == filters["state"])
        if cursor:
            result = await self.session.execute(
                select(Institution.id).where(Institution.public_id == cursor)
            )
            cursor_id = result.scalar_one_or_none()
            if cursor_id is not None:
                stmt = stmt.where(Institution.id < cursor_id)
        result = await self.session.execute(stmt)
        return cast("list[Institution]", result.unique().scalars().all())

    async def get_member(self, institution_id: int, user_id: int) -> InstitutionMember | None:
        result = await self.session.execute(
            select(InstitutionMember)
            .options(selectinload(InstitutionMember.user))
            .where(
                InstitutionMember.institution_id == institution_id,
                InstitutionMember.user_id == user_id,
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_member_by_public_id(
        self, institution_id: int, user_public_id: str
    ) -> InstitutionMember | None:
        from oldpages_api.identity.models import User

        result = await self.session.execute(
            select(InstitutionMember)
            .join(User, User.id == InstitutionMember.user_id)
            .options(selectinload(InstitutionMember.user))
            .where(
                InstitutionMember.institution_id == institution_id,
                User.public_id == user_public_id,
            )
        )
        return result.unique().scalar_one_or_none()

    async def list_members(
        self,
        institution_id: int,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[InstitutionMember]:
        stmt = (
            select(InstitutionMember)
            .options(selectinload(InstitutionMember.user))
            .where(InstitutionMember.institution_id == institution_id)
            .order_by(InstitutionMember.id.asc())
            .limit(limit)
        )
        if cursor:
            result = await self.session.execute(
                select(InstitutionMember.id).where(InstitutionMember.public_id == cursor)
            )
            cursor_id = result.scalar_one_or_none()
            if cursor_id is not None:
                stmt = stmt.where(InstitutionMember.id > cursor_id)
        result = await self.session.execute(stmt)
        return cast("list[InstitutionMember]", result.unique().scalars().all())

    async def get_domain(self, domain: str) -> InstitutionDomain | None:
        result = await self.session.execute(
            select(InstitutionDomain).where(InstitutionDomain.domain == domain)
        )
        return result.scalar_one_or_none()

    async def list_domains(self, institution_id: int) -> list[InstitutionDomain]:
        result = await self.session.execute(
            select(InstitutionDomain).where(InstitutionDomain.institution_id == institution_id)
        )
        return list(result.scalars().all())

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def institution_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Institution.owner),
        selectinload(Institution.domains),
        selectinload(Institution.members).selectinload(InstitutionMember.user),
    )


__all__ = ["InstitutionRepository"]
