from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from oldpages_api.shared.db.database import get_session
from oldpages_api.trust.schemas import (
    ConversationEvidenceResponse,
    ModerationActionRequest,
    ModerationCaseListResponse,
    ModerationCaseResponse,
    ModerationListingResponse,
    ModerationRuleConfigResponse,
    ModerationUserResponse,
    ReportAppealRequest,
    ReportCreateRequest,
    ReportResponse,
)
from oldpages_api.trust.service import TrustService

reports_router = APIRouter(prefix="/reports", tags=["reports"])
admin_moderation_router = APIRouter(prefix="/admin/moderation", tags=["admin-moderation"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def trust_service(session: AsyncSession) -> TrustService:
    return TrustService(session)


@reports_router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReportResponse:
    return await trust_service(session).create_report(
        payload,
        principal.user,
        request_context(request),
    )


@reports_router.post("/{report_id}/appeal", response_model=ReportResponse)
async def appeal_report(
    report_id: str,
    payload: ReportAppealRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReportResponse:
    return await trust_service(session).appeal_report(
        report_id,
        payload,
        principal.user,
        request_context(request),
    )


@admin_moderation_router.get("/cases", response_model=ModerationCaseListResponse)
async def list_moderation_cases(
    principal: PrincipalDep,
    session: SessionDep,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    status: str | None = None,
) -> ModerationCaseListResponse:
    return await trust_service(session).list_cases(
        principal.user,
        cursor=cursor,
        limit=limit,
        status=status,
    )


@admin_moderation_router.get("/cases/{case_id}", response_model=ModerationCaseResponse)
async def get_moderation_case(
    case_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> ModerationCaseResponse:
    return await trust_service(session).get_case(case_id, principal.user)


@admin_moderation_router.post("/cases/{case_id}/actions", response_model=ModerationCaseResponse)
async def take_moderation_action(
    case_id: str,
    payload: ModerationActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ModerationCaseResponse:
    return await trust_service(session).take_action(
        case_id,
        payload,
        principal.user,
        request_context(request),
    )


@admin_moderation_router.get(
    "/cases/{case_id}/conversation-evidence",
    response_model=ConversationEvidenceResponse,
)
async def get_conversation_evidence(
    case_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ConversationEvidenceResponse:
    return await trust_service(session).conversation_evidence(
        case_id,
        principal.user,
        request_context(request),
    )


@admin_moderation_router.get("/users/{user_id}", response_model=ModerationUserResponse)
async def get_moderation_user(
    user_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> ModerationUserResponse:
    return await trust_service(session).moderation_user(user_id, principal.user)


@admin_moderation_router.get("/listings/{listing_id}", response_model=ModerationListingResponse)
async def get_moderation_listing(
    listing_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> ModerationListingResponse:
    return await trust_service(session).moderation_listing(listing_id, principal.user)


@admin_moderation_router.get("/rules", response_model=ModerationRuleConfigResponse)
async def get_moderation_rules(
    principal: PrincipalDep,
    session: SessionDep,
) -> ModerationRuleConfigResponse:
    return await trust_service(session).rules(principal.user)
