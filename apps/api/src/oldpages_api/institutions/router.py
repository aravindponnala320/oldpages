from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import CurrentPrincipal, get_current_principal, get_moderator_principal
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
)
from oldpages_api.institutions.service import InstitutionService
from oldpages_api.shared.db.database import get_session

institutions_router = APIRouter(prefix="/institutions", tags=["institutions"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]
ModeratorDep = Annotated[CurrentPrincipal, Depends(get_moderator_principal)]


def institution_service(session: AsyncSession) -> InstitutionService:
    return InstitutionService(session)


@institutions_router.post(
    "",
    response_model=InstitutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_institution(
    payload: InstitutionCreateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> InstitutionResponse:
    return await institution_service(session).create_institution(payload, principal.user)


@institutions_router.get("", response_model=InstitutionListResponse)
async def list_institutions(
    session: SessionDep,
    type: str | None = Query(default=None),
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> InstitutionListResponse:
    filters = {"type": type, "city": city, "state": state}
    return await institution_service(session).list_institutions(filters, limit=limit, cursor=cursor)


@institutions_router.get("/pending", response_model=InstitutionListResponse)
async def list_pending_institutions(
    principal: ModeratorDep,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> InstitutionListResponse:
    return await institution_service(session).list_pending_institutions(limit=limit, cursor=cursor)


@institutions_router.post("/{institution_id}/approve", response_model=InstitutionResponse)
async def approve_institution(
    institution_id: str,
    principal: ModeratorDep,
    session: SessionDep,
) -> InstitutionResponse:
    return await institution_service(session).approve_institution(institution_id, principal.user)


@institutions_router.post("/{institution_id}/reject", response_model=InstitutionResponse)
async def reject_institution(
    institution_id: str,
    payload: ApprovalActionRequest,
    principal: ModeratorDep,
    session: SessionDep,
) -> InstitutionResponse:
    return await institution_service(session).reject_institution(
        institution_id, payload, principal.user
    )


@institutions_router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(
    institution_id: str,
    session: SessionDep,
) -> InstitutionResponse:
    return await institution_service(session).get_institution(institution_id)


@institutions_router.patch("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(
    institution_id: str,
    payload: InstitutionUpdateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> InstitutionResponse:
    return await institution_service(session).update_institution(
        institution_id, payload, principal.user
    )


@institutions_router.post(
    "/{institution_id}/join",
    response_model=InstitutionMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def join_institution(
    institution_id: str,
    payload: JoinInstitutionRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> InstitutionMemberResponse:
    return await institution_service(session).join_institution(
        institution_id, payload, principal.user
    )


@institutions_router.get(
    "/{institution_id}/members",
    response_model=list[InstitutionMemberResponse],
)
async def list_members(
    institution_id: str,
    principal: PrincipalDep,
    session: SessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> list[InstitutionMemberResponse]:
    return await institution_service(session).list_members(
        institution_id, principal.user, limit=limit, cursor=cursor
    )


@institutions_router.post(
    "/{institution_id}/approve-member",
    response_model=InstitutionMemberResponse,
)
async def approve_member(
    institution_id: str,
    payload: ApproveMemberRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> InstitutionMemberResponse:
    return await institution_service(session).approve_member(
        institution_id, payload, principal.user
    )


@institutions_router.delete(
    "/{institution_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    institution_id: str,
    user_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> None:
    await institution_service(session).remove_member(institution_id, user_id, principal.user)


@institutions_router.post(
    "/{institution_id}/domains",
    response_model=InstitutionDomainResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_domain(
    institution_id: str,
    payload: AddDomainRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> InstitutionDomainResponse:
    return await institution_service(session).add_domain(institution_id, payload, principal.user)


@institutions_router.post(
    "/{institution_id}/domains/{domain}/verify",
    response_model=InstitutionDomainResponse,
)
async def verify_domain(
    institution_id: str,
    domain: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> InstitutionDomainResponse:
    return await institution_service(session).verify_domain(
        institution_id,
        domain.strip().lower(),
        principal.user,
    )


@institutions_router.post(
    "/{institution_id}/verify",
    response_model=InstitutionResponse,
)
async def verify_institution(
    institution_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> InstitutionResponse:
    return await institution_service(session).verify_institution(institution_id, principal.user)
