from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from oldpages_api.identity.schemas import (
    BlockRequest,
    BlockResponse,
    DeviceResponse,
    RequestAcceptedResponse,
    SessionResponse,
    UpdateMeRequest,
    UserPrivateResponse,
    UserPublicResponse,
)
from oldpages_api.identity.service import IdentityService
from oldpages_api.shared.db.database import get_session

router = APIRouter(prefix="/users", tags=["users"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def identity_service(request: Request, session: AsyncSession) -> IdentityService:
    return IdentityService(session, request.app.state.settings)


@router.get("/me", response_model=UserPrivateResponse)
async def get_me(
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> UserPrivateResponse:
    return await identity_service(request, session).private_user_response(principal.user)


@router.patch("/me", response_model=UserPrivateResponse)
async def update_me(
    payload: UpdateMeRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> UserPrivateResponse:
    return await identity_service(request, session).update_me(
        principal.user,
        payload,
        request_context(request),
    )


@router.get("/me/sessions", response_model=list[SessionResponse])
async def list_my_sessions(
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> list[SessionResponse]:
    sessions = await identity_service(request, session).list_sessions(
        principal.user,
        principal.session_public_id,
    )
    return [
        SessionResponse(
            created_at=item.created_at,
            current=getattr(item, "_current", False),
            id=item.public_id,
            last_used_at=item.last_used_at,
            revoked_at=item.revoked_at,
            user_agent=item.user_agent,
        )
        for item in sessions
    ]


@router.delete("/me/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_my_session(
    session_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    await identity_service(request, session).revoke_session(
        principal.user,
        session_id,
        request_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/devices", response_model=list[DeviceResponse])
async def list_my_devices(
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> list[DeviceResponse]:
    devices = await identity_service(request, session).list_devices(principal.user)
    return [
        DeviceResponse(
            created_at=item.created_at,
            device_name=item.device_name,
            device_type=item.device_type,
            id=item.public_id,
            last_seen_at=item.last_seen_at,
        )
        for item in devices
    ]


@router.post("/me/delete-request", response_model=RequestAcceptedResponse)
async def request_account_deletion(
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> RequestAcceptedResponse:
    return await identity_service(request, session).request_account_deletion(
        principal.user,
        request_context(request),
    )


@router.post("/me/export-request", response_model=RequestAcceptedResponse)
async def request_data_export(
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> RequestAcceptedResponse:
    return await identity_service(request, session).request_data_export(
        principal.user,
        request_context(request),
    )


@router.get("/{user_id}", response_model=UserPublicResponse)
async def get_public_user(
    user_id: str,
    request: Request,
    session: SessionDep,
) -> UserPublicResponse:
    return await identity_service(request, session).public_user_response(user_id)


@router.post("/{user_id}/block", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def block_user(
    user_id: str,
    payload: BlockRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> BlockResponse:
    block = await identity_service(request, session).block_user(
        actor=principal.user,
        blocked_public_id=user_id,
        reason=payload.reason,
        context=request_context(request),
    )
    return BlockResponse(blocked_user_id=user_id, id=block.public_id)


@router.delete("/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    user_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    await identity_service(request, session).unblock_user(
        actor=principal.user,
        blocked_public_id=user_id,
        context=request_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
