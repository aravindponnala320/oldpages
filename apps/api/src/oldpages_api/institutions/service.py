from __future__ import annotations

import re
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.models import User
from oldpages_api.identity.security import utc_now
from oldpages_api.institutions.events import (
    INSTITUTION_CREATED,
    INSTITUTION_MEMBER_APPROVED,
    INSTITUTION_MEMBER_JOINED,
    INSTITUTION_VERIFIED,
)
from oldpages_api.institutions.exceptions import (
    AlreadyMemberError,
    InstitutionMemberNotFoundError,
    InstitutionNotFoundError,
    InstitutionValidationError,
)
from oldpages_api.institutions.models import (
    Institution,
    InstitutionDomain,
    InstitutionMember,
)
from oldpages_api.institutions.permissions import require_institution_admin
from oldpages_api.institutions.repository import InstitutionRepository
from oldpages_api.institutions.schemas import (
    AddDomainRequest,
    ApproveMemberRequest,
    ApprovalActionRequest,
    InstitutionCreateRequest,
    InstitutionDomainResponse,
    InstitutionListResponse,
    InstitutionMemberResponse,
    InstitutionResponse,
    InstitutionUpdateRequest,
    JoinInstitutionRequest,
    MemberRole,
    MemberStatus,
)


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug[:260]


class InstitutionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = InstitutionRepository(session)

    async def create_institution(
        self,
        payload: InstitutionCreateRequest,
        actor: User,
    ) -> InstitutionResponse:
        existing_own = await self.repo.get_institution_by_owner(actor.id)
        if existing_own is not None:
            raise InstitutionValidationError(
                "You already have an institution. Each user can only create one."
            )
        base_slug = slugify(payload.name)
        slug = base_slug
        existing = await self.repo.get_institution_by_slug(slug)
        if existing is not None:
            slug = f"{base_slug}-{actor.id}"
        institution = Institution(
            city=payload.city,
            country="IN",
            description=payload.description,
            is_verified=False,
            member_count=0,
            name=payload.name,
            owner_user_id=actor.id,
            slug=slug,
            state=payload.state,
            status="pending",
            type=payload.type,
            website=payload.website,
        )
        self.repo.add(institution)
        await self.repo.flush()
        owner_member = InstitutionMember(
            email_verified=False,
            institution_id=institution.id,
            joined_at=utc_now(),
            role="admin",
            status="active",
            user_id=actor.id,
        )
        self.repo.add(owner_member)
        await self.repo.commit()
        reloaded = await self.repo.get_institution_by_id(institution.id)
        if reloaded is None:
            raise InstitutionValidationError("Institution could not be loaded.")
        _ = INSTITUTION_CREATED
        return institution_response(reloaded)

    async def get_institution(self, institution_id_or_slug: str) -> InstitutionResponse:
        institution = await self.repo.get_institution_by_public_id(institution_id_or_slug)
        if institution is None:
            institution = await self.repo.get_institution_by_slug(institution_id_or_slug)
        if institution is None:
            raise InstitutionNotFoundError()
        return institution_response(institution)

    async def list_institutions(
        self,
        filters: dict[str, str | None],
        limit: int = 20,
        cursor: str | None = None,
    ) -> InstitutionListResponse:
        institutions = await self.repo.list_institutions(filters, limit=limit, cursor=cursor)
        next_cursor = institutions[-1].public_id if len(institutions) == limit else None
        return InstitutionListResponse(
            items=[institution_response(i) for i in institutions],
            next_cursor=next_cursor,
        )

    async def update_institution(
        self,
        institution_id: str,
        payload: InstitutionUpdateRequest,
        actor: User,
    ) -> InstitutionResponse:
        institution = await self.get_institution_model(institution_id)
        member_map = {m.user_id: m for m in institution.members}
        require_institution_admin(institution, actor, member_map)
        if payload.name is not None:
            institution.name = payload.name
        if payload.description is not None:
            institution.description = payload.description
        if payload.website is not None:
            institution.website = payload.website
        if payload.logo_url is not None:
            institution.logo_url = payload.logo_url
        if payload.cover_url is not None:
            institution.cover_url = payload.cover_url
        if payload.city is not None:
            institution.city = payload.city
        if payload.state is not None:
            institution.state = payload.state
        await self.repo.commit()
        reloaded = await self.repo.get_institution_by_id(institution.id)
        if reloaded is None:
            raise InstitutionValidationError("Institution could not be loaded.")
        return institution_response(reloaded)

    async def join_institution(
        self,
        institution_id: str,
        payload: JoinInstitutionRequest,
        actor: User,
    ) -> InstitutionMemberResponse:
        institution = await self.get_institution_model(institution_id)
        existing = await self.repo.get_member(institution.id, actor.id)
        if existing is not None:
            raise AlreadyMemberError()
        member = InstitutionMember(
            email_verified=False,
            institution_id=institution.id,
            role=payload.role,
            status="pending",
            user_id=actor.id,
        )
        self.repo.add(member)
        await self.repo.commit()
        reloaded = await self.repo.get_member(institution.id, actor.id)
        if reloaded is None:
            raise InstitutionValidationError("Member could not be loaded.")
        _ = INSTITUTION_MEMBER_JOINED
        return member_response(reloaded, institution)

    async def approve_member(
        self,
        institution_id: str,
        payload: ApproveMemberRequest,
        actor: User,
    ) -> InstitutionMemberResponse:
        institution = await self.get_institution_model(institution_id)
        member_map = {m.user_id: m for m in institution.members}
        require_institution_admin(institution, actor, member_map)
        target_member = await self.repo.get_member_by_public_id(institution.id, payload.user_id)
        if target_member is None:
            raise InstitutionMemberNotFoundError()
        if target_member.status == "active":
            return member_response(target_member, institution)
        target_member.status = "active"
        target_member.joined_at = utc_now()
        institution.member_count = institution.member_count + 1
        await self.repo.commit()
        reloaded = await self.repo.get_member(institution.id, target_member.user_id)
        if reloaded is None:
            raise InstitutionMemberNotFoundError()
        _ = INSTITUTION_MEMBER_APPROVED
        return member_response(reloaded, institution)

    async def remove_member(
        self,
        institution_id: str,
        user_id: str,
        actor: User,
    ) -> None:
        institution = await self.get_institution_model(institution_id)
        member_map = {m.user_id: m for m in institution.members}
        require_institution_admin(institution, actor, member_map)
        target_member = await self.repo.get_member_by_public_id(institution.id, user_id)
        if target_member is None:
            raise InstitutionMemberNotFoundError()
        if target_member.status == "active" and institution.member_count > 0:
            institution.member_count = institution.member_count - 1
        await self.repo.delete(target_member)
        await self.repo.commit()

    async def add_domain(
        self,
        institution_id: str,
        payload: AddDomainRequest,
        actor: User,
    ) -> InstitutionDomainResponse:
        institution = await self.get_institution_model(institution_id)
        member_map = {m.user_id: m for m in institution.members}
        require_institution_admin(institution, actor, member_map)
        existing = await self.repo.get_domain(payload.domain)
        if existing is not None:
            raise InstitutionValidationError("Domain is already registered.")
        domain = InstitutionDomain(
            domain=payload.domain,
            institution_id=institution.id,
            is_verified=False,
        )
        self.repo.add(domain)
        await self.repo.commit()
        return domain_response(domain, institution)

    async def verify_domain(
        self,
        institution_id: str,
        domain: str,
        actor: User,
    ) -> InstitutionDomainResponse:
        institution = await self.get_institution_model(institution_id)
        member_map = {m.user_id: m for m in institution.members}
        require_institution_admin(institution, actor, member_map)
        domain_obj = await self.repo.get_domain(domain)
        if domain_obj is None or domain_obj.institution_id != institution.id:
            raise InstitutionValidationError("Domain not found for this institution.")
        domain_obj.is_verified = True
        domain_obj.verified_at = utc_now()
        await self.repo.commit()
        return domain_response(domain_obj, institution)

    async def verify_institution(
        self,
        institution_id: str,
        actor: User,
    ) -> InstitutionResponse:
        institution = await self.get_institution_model(institution_id)
        member_map = {m.user_id: m for m in institution.members}
        require_institution_admin(institution, actor, member_map)
        institution.is_verified = True
        institution.verified_at = utc_now()
        institution.status = "active"
        await self.repo.commit()
        reloaded = await self.repo.get_institution_by_id(institution.id)
        if reloaded is None:
            raise InstitutionValidationError("Institution could not be loaded.")
        _ = INSTITUTION_VERIFIED
        return institution_response(reloaded)

    async def list_members(
        self,
        institution_id: str,
        actor: User,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[InstitutionMemberResponse]:
        institution = await self.get_institution_model(institution_id)
        member_map = {m.user_id: m for m in institution.members}
        require_institution_admin(institution, actor, member_map)
        members = await self.repo.list_members(institution.id, limit=limit, cursor=cursor)
        return [member_response(m, institution) for m in members]

    async def approve_institution(
        self,
        institution_id: str,
        actor: User,
    ) -> InstitutionResponse:
        institution = await self.get_institution_model(institution_id)
        if institution.status == "active":
            return institution_response(institution)
        institution.status = "active"
        institution.rejected_reason = None
        institution.reviewed_by_user_id = actor.id
        institution.reviewed_at = utc_now()
        await self.repo.commit()
        reloaded = await self.repo.get_institution_by_id(institution.id)
        if reloaded is None:
            raise InstitutionValidationError("Institution could not be loaded.")
        return institution_response(reloaded)

    async def reject_institution(
        self,
        institution_id: str,
        payload: ApprovalActionRequest,
        actor: User,
    ) -> InstitutionResponse:
        institution = await self.get_institution_model(institution_id)
        institution.status = "rejected"
        institution.rejected_reason = payload.reason
        institution.reviewed_by_user_id = actor.id
        institution.reviewed_at = utc_now()
        await self.repo.commit()
        reloaded = await self.repo.get_institution_by_id(institution.id)
        if reloaded is None:
            raise InstitutionValidationError("Institution could not be loaded.")
        return institution_response(reloaded)

    async def list_pending_institutions(
        self,
        limit: int = 50,
        cursor: str | None = None,
    ) -> InstitutionListResponse:
        institutions = await self.repo.list_institutions(
            {"status": "pending"}, limit=limit, cursor=cursor
        )
        next_cursor = institutions[-1].public_id if len(institutions) == limit else None
        return InstitutionListResponse(
            items=[institution_response(i) for i in institutions],
            next_cursor=next_cursor,
        )

    async def get_institution_model(self, institution_id: str) -> Institution:
        institution = await self.repo.get_institution_by_public_id(institution_id)
        if institution is None:
            raise InstitutionNotFoundError()
        return institution


def institution_response(institution: Institution) -> InstitutionResponse:
    from oldpages_api.institutions.schemas import InstitutionStatus, InstitutionType

    return InstitutionResponse(
        city=institution.city,
        country=institution.country,
        cover_url=institution.cover_url,
        created_at=institution.created_at,
        description=institution.description,
        id=institution.public_id,
        is_verified=institution.is_verified,
        logo_url=institution.logo_url,
        member_count=institution.member_count,
        name=institution.name,
        owner_user_id=institution.owner.public_id if institution.owner else None,
        rejected_reason=institution.rejected_reason,
        slug=institution.slug,
        state=institution.state,
        status=cast("InstitutionStatus", institution.status),
        type=cast("InstitutionType", institution.type),
        updated_at=institution.updated_at,
        verified_at=institution.verified_at,
        website=institution.website,
    )


def member_response(
    member: InstitutionMember,
    institution: Institution,
) -> InstitutionMemberResponse:
    return InstitutionMemberResponse(
        created_at=member.created_at,
        email_verified=member.email_verified,
        id=member.public_id,
        institution_id=institution.public_id,
        joined_at=member.joined_at,
        role=cast("MemberRole", member.role),
        status=cast("MemberStatus", member.status),
        user_id=member.user.public_id,
    )


def domain_response(
    domain: InstitutionDomain,
    institution: Institution,
) -> InstitutionDomainResponse:
    return InstitutionDomainResponse(
        created_at=domain.created_at,
        domain=domain.domain,
        id=domain.public_id,
        institution_id=institution.public_id,
        is_verified=domain.is_verified,
        verified_at=domain.verified_at,
    )
