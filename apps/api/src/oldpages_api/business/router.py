from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.business.schemas import (
    ApprovalActionRequest,
    BusinessLocationCreateRequest,
    BusinessLocationResponse,
    BusinessProfileCreateRequest,
    BusinessProfileResponse,
    BusinessProfileUpdateRequest,
    InventoryImportCreateRequest,
    InventoryImportResponse,
    StaffAccountResponse,
    StaffInviteRequest,
)
from oldpages_api.business.service import BusinessService
from oldpages_api.identity.dependencies import CurrentPrincipal, get_current_principal, get_moderator_principal
from oldpages_api.shared.db.database import get_session

business_router = APIRouter(prefix="/business", tags=["business"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]
ModeratorDep = Annotated[CurrentPrincipal, Depends(get_moderator_principal)]


def business_service(session: AsyncSession) -> BusinessService:
    return BusinessService(session)


@business_router.post(
    "",
    response_model=BusinessProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    payload: BusinessProfileCreateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> BusinessProfileResponse:
    return await business_service(session).create_profile(payload, principal.user)


@business_router.get("/me", response_model=BusinessProfileResponse | None)
async def get_my_profile(
    principal: PrincipalDep,
    session: SessionDep,
) -> BusinessProfileResponse | None:
    return await business_service(session).get_my_profile(principal.user)


@business_router.get("/pending", response_model=list[BusinessProfileResponse])
async def list_pending_profiles(
    principal: ModeratorDep,
    session: SessionDep,
    limit: int = 50,
    cursor: str | None = None,
) -> list[BusinessProfileResponse]:
    return await business_service(session).list_pending_profiles(limit=limit, cursor=cursor)


@business_router.get("", response_model=list[BusinessProfileResponse])
async def list_profiles(
    session: SessionDep,
    type: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> list[BusinessProfileResponse]:
    filters = {}
    if type is not None:
        filters["type"] = type
    return await business_service(session).list_profiles(filters or None, limit, cursor)


@business_router.get("/{profile_id}", response_model=BusinessProfileResponse)
async def get_profile(
    profile_id: str,
    session: SessionDep,
) -> BusinessProfileResponse:
    return await business_service(session).get_profile(profile_id)


@business_router.patch("/{profile_id}", response_model=BusinessProfileResponse)
async def update_profile(
    profile_id: str,
    payload: BusinessProfileUpdateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> BusinessProfileResponse:
    return await business_service(session).update_profile(profile_id, payload, principal.user)


@business_router.post(
    "/{profile_id}/locations",
    response_model=BusinessLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_location(
    profile_id: str,
    payload: BusinessLocationCreateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> BusinessLocationResponse:
    return await business_service(session).add_location(profile_id, payload, principal.user)


@business_router.delete(
    "/{profile_id}/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_location(
    profile_id: str,
    location_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> None:
    await business_service(session).remove_location(location_id, principal.user)


@business_router.get("/{profile_id}/staff", response_model=list[StaffAccountResponse])
async def list_staff(
    profile_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> list[StaffAccountResponse]:
    svc = business_service(session)
    profile = await svc.repo.get_profile_by_public_id(profile_id)
    from oldpages_api.business.exceptions import BusinessProfileNotFoundError
    from oldpages_api.business.permissions import require_business_permission
    from oldpages_api.business.service import staff_response

    if profile is None:
        raise BusinessProfileNotFoundError()
    require_business_permission(profile, principal.user, "manage_staff")
    staff_list = await svc.repo.list_staff(profile.id)
    return [staff_response(s) for s in staff_list]


@business_router.post(
    "/{profile_id}/staff",
    response_model=StaffAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_staff(
    profile_id: str,
    payload: StaffInviteRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> StaffAccountResponse:
    return await business_service(session).invite_staff(profile_id, payload, principal.user)


@business_router.delete(
    "/{profile_id}/staff/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_staff(
    profile_id: str,
    user_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> None:
    await business_service(session).remove_staff(profile_id, user_id, principal.user)


@business_router.post("/{profile_id}/approve", response_model=BusinessProfileResponse)
async def approve_profile(
    profile_id: str,
    principal: ModeratorDep,
    session: SessionDep,
) -> BusinessProfileResponse:
    return await business_service(session).approve_profile(profile_id, principal.user)


@business_router.post("/{profile_id}/reject", response_model=BusinessProfileResponse)
async def reject_profile(
    profile_id: str,
    payload: ApprovalActionRequest,
    principal: ModeratorDep,
    session: SessionDep,
) -> BusinessProfileResponse:
    return await business_service(session).reject_profile(profile_id, payload, principal.user)


@business_router.post(
    "/{profile_id}/imports",
    response_model=InventoryImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_import(
    profile_id: str,
    payload: InventoryImportCreateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> InventoryImportResponse:
    return await business_service(session).create_import(profile_id, payload, principal.user)


@business_router.get(
    "/{profile_id}/imports/{import_id}",
    response_model=InventoryImportResponse,
)
async def get_import_status(
    profile_id: str,
    import_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> InventoryImportResponse:
    return await business_service(session).get_import_status(
        profile_id,
        import_id,
        principal.user,
    )


@business_router.get("/{profile_id}/imports/{import_id}/errors.csv")
async def get_import_error_report(
    profile_id: str,
    import_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> PlainTextResponse:
    csv_body = await business_service(session).get_import_error_report(
        profile_id,
        import_id,
        principal.user,
    )
    return PlainTextResponse(
        csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{import_id}-errors.csv"'},
    )
