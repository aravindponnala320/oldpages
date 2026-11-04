from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from oldpages_api.notifications.schemas import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
    NotificationResponse,
)
from oldpages_api.notifications.service import NotificationService
from oldpages_api.shared.db.database import get_session

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
notification_preferences_router = APIRouter(
    prefix="/notification-preferences",
    tags=["notification preferences"],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def notification_service(session: AsyncSession) -> NotificationService:
    return NotificationService(session)


@notifications_router.get("", response_model=NotificationListResponse)
async def list_notifications(
    principal: PrincipalDep,
    session: SessionDep,
    cursor: str | None = Query(default=None, max_length=26),
    limit: int = Query(default=20, ge=1, le=50),
) -> NotificationListResponse:
    return await notification_service(session).list_notifications(
        principal.user,
        cursor=cursor,
        limit=limit,
    )


@notifications_router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> NotificationResponse:
    return await notification_service(session).mark_notification_read(
        notification_id,
        principal.user,
        request_context(request),
    )


@notification_preferences_router.get("", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    principal: PrincipalDep,
    session: SessionDep,
) -> NotificationPreferenceResponse:
    return await notification_service(session).get_or_create_preferences(principal.user)


@notification_preferences_router.patch("", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    payload: NotificationPreferenceUpdateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> NotificationPreferenceResponse:
    return await notification_service(session).update_preferences(
        payload,
        principal.user,
        request_context(request),
    )
