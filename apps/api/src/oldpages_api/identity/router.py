from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from oldpages_api.identity.exceptions import ForbiddenIdentityActionError, InvalidTokenError
from oldpages_api.identity.schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MobileVerificationRequest,
    OAuthRequest,
    RefreshRequest,
    RegisterRequest,
    RequestAcceptedResponse,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from oldpages_api.identity.service import IdentityService
from oldpages_api.shared.db.database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def identity_service(request: Request, session: AsyncSession) -> IdentityService:
    return IdentityService(session, request.app.state.settings)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    session: SessionDep,
) -> AuthResponse:
    return await identity_service(request, session).register(payload, request_context(request))


@router.post("/register/superuser", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_superuser(
    payload: RegisterRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> AuthResponse:
    if not principal.user.is_superuser:
        raise ForbiddenIdentityActionError("Only superusers can create superuser accounts.")
    return await identity_service(request, session).register_superuser(payload, request_context(request))


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: SessionDep,
) -> AuthResponse:
    return await identity_service(request, session).login(payload, request_context(request))


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    session: SessionDep,
) -> AuthResponse:
    return await identity_service(request, session).refresh(
        payload.refresh_token, request_context(request)
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    request: Request,
    session: SessionDep,
) -> Response:
    await identity_service(request, session).logout(payload.refresh_token, request_context(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    await identity_service(request, session).logout_all(principal.user, request_context(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    session: SessionDep,
) -> Response:
    await identity_service(request, session).verify_email(payload.token, request_context(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", response_model=RequestAcceptedResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    session: SessionDep,
) -> RequestAcceptedResponse:
    return await identity_service(request, session).forgot_password(
        payload.email,
        request_context(request),
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    session: SessionDep,
) -> Response:
    await identity_service(request, session).reset_password(
        token=payload.token,
        new_password=payload.new_password,
        context=request_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/oauth/{provider}", response_model=AuthResponse)
async def oauth_login(
    provider: Literal["google", "apple"],
    payload: OAuthRequest,
    request: Request,
    session: SessionDep,
) -> AuthResponse:
    if provider not in {"google", "apple"}:
        raise InvalidTokenError("OAuth provider is not supported.")
    return await identity_service(request, session).oauth_login(
        provider,
        payload,
        request_context(request),
    )


@router.post("/request-mobile-verification", response_model=RequestAcceptedResponse)
async def request_mobile_verification(
    payload: MobileVerificationRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> RequestAcceptedResponse:
    return await identity_service(request, session).request_mobile_verification(
        principal.user,
        payload.mobile_number,
        request_context(request),
    )
