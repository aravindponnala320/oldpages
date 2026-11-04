from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.core.errors import AppError
from oldpages_api.identity.exceptions import UnauthorizedError
from oldpages_api.identity.models import User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.service import IdentityService
from oldpages_api.shared.db.database import get_session

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class CurrentPrincipal:
    session_public_id: str
    user: User


def request_context(request: Request) -> AuthenticatedRequestContext:
    return AuthenticatedRequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


async def get_current_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    service = IdentityService(session, request.app.state.settings)
    user, session_public_id = await service.get_user_from_access_token(credentials.credentials)
    return CurrentPrincipal(user=user, session_public_id=session_public_id)


async def get_optional_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentPrincipal | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    service = IdentityService(session, request.app.state.settings)
    user, session_public_id = await service.get_user_from_access_token(credentials.credentials)
    return CurrentPrincipal(user=user, session_public_id=session_public_id)


async def get_current_user(
    principal: Annotated[CurrentPrincipal, Depends(get_current_principal)],
) -> User:
    return principal.user


class ForbiddenModeratorError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Moderator role is required.",
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


async def get_moderator_principal(
    principal: Annotated[CurrentPrincipal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentPrincipal:
    from sqlalchemy import select as sa_select

    from oldpages_api.identity.models import UserPreference

    result = await session.execute(
        sa_select(UserPreference).where(UserPreference.user_id == principal.user.id)
    )
    prefs = result.scalar_one_or_none()
    roles: list[str] = []
    if prefs is not None:
        roles = prefs.metadata_json.get("roles", [])
    moderator_roles = {"admin", "moderator", "trust_moderator"}
    if not (principal.user.is_superuser or bool(moderator_roles & set(roles))):
        raise ForbiddenModeratorError()
    return principal
