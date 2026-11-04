from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.communities.schemas import (
    CommunityApproveMemberRequest,
    CommunityCreateRequest,
    CommunityFeedResponse,
    CommunityJoinRequest,
    CommunityListResponse,
    CommunityMarketplaceResponse,
    CommunityMemberResponse,
    CommunityPostCreateRequest,
    CommunityPostResponse,
    CommunityReportCreateRequest,
    CommunityReportResponse,
    CommunityResponse,
    PostCommentCreateRequest,
    PostCommentResponse,
    PostReactionRequest,
    PostReactionResponse,
)
from oldpages_api.communities.service import CommunityService
from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    get_optional_principal,
    request_context,
)
from oldpages_api.shared.db.database import get_session

communities_router = APIRouter(prefix="/communities", tags=["communities"])
posts_router = APIRouter(prefix="/posts", tags=["community posts"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]
OptionalPrincipalDep = Annotated[CurrentPrincipal | None, Depends(get_optional_principal)]


def community_service(session: AsyncSession) -> CommunityService:
    return CommunityService(session)


@communities_router.post(
    "",
    response_model=CommunityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_community(
    payload: CommunityCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> CommunityResponse:
    return await community_service(session).create_community(
        payload,
        principal.user,
        request_context(request),
    )


@communities_router.get("", response_model=CommunityListResponse)
async def list_communities(
    request: Request,
    session: SessionDep,
    principal: OptionalPrincipalDep,
    book_id: str | None = Query(default=None),
    city: str | None = Query(default=None),
    country: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    genre: str | None = Query(default=None),
    institution: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> CommunityListResponse:
    del request
    return await community_service(session).list_communities(
        book_id=book_id,
        city=city,
        country=country,
        cursor=cursor,
        genre=genre,
        institution=institution,
        limit=limit,
        viewer=principal.user if principal else None,
    )


@communities_router.get("/{community_id}", response_model=CommunityResponse)
async def get_community(
    community_id: str,
    session: SessionDep,
    principal: OptionalPrincipalDep,
) -> CommunityResponse:
    return await community_service(session).get_community(
        community_id,
        principal.user if principal else None,
    )


@communities_router.post("/{community_id}/join", response_model=CommunityMemberResponse)
async def join_community(
    community_id: str,
    payload: CommunityJoinRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> CommunityMemberResponse:
    return await community_service(session).join_community(
        community_id,
        payload,
        principal.user,
        request_context(request),
    )


@communities_router.post("/{community_id}/approve-member", response_model=CommunityMemberResponse)
async def approve_member(
    community_id: str,
    payload: CommunityApproveMemberRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> CommunityMemberResponse:
    return await community_service(session).approve_member(
        community_id,
        payload,
        principal.user,
        request_context(request),
    )


@communities_router.post("/{community_id}/posts", response_model=CommunityPostResponse)
async def create_post(
    community_id: str,
    payload: CommunityPostCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> CommunityPostResponse:
    return await community_service(session).create_post(
        community_id,
        payload,
        principal.user,
        request_context(request),
    )


@communities_router.get("/{community_id}/feed", response_model=CommunityFeedResponse)
async def get_feed(
    community_id: str,
    session: SessionDep,
    principal: OptionalPrincipalDep,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> CommunityFeedResponse:
    return await community_service(session).get_feed(
        community_id,
        cursor=cursor,
        limit=limit,
        viewer=principal.user if principal else None,
    )


@communities_router.get("/{community_id}/marketplace", response_model=CommunityMarketplaceResponse)
async def get_marketplace(
    community_id: str,
    session: SessionDep,
    principal: OptionalPrincipalDep,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> CommunityMarketplaceResponse:
    return await community_service(session).marketplace(
        community_id,
        cursor=cursor,
        limit=limit,
        viewer=principal.user if principal else None,
    )


@communities_router.post("/{community_id}/reports", response_model=CommunityReportResponse)
async def create_report(
    community_id: str,
    payload: CommunityReportCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> CommunityReportResponse:
    return await community_service(session).create_report(
        community_id,
        payload,
        principal.user,
        request_context(request),
    )


@posts_router.post("/{post_id}/comments", response_model=PostCommentResponse)
async def create_comment(
    post_id: str,
    payload: PostCommentCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> PostCommentResponse:
    return await community_service(session).create_comment(
        post_id,
        payload,
        principal.user,
        request_context(request),
    )


@posts_router.post("/{post_id}/reactions", response_model=PostReactionResponse)
async def set_reaction(
    post_id: str,
    payload: PostReactionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> PostReactionResponse:
    return await community_service(session).set_reaction(
        post_id,
        payload,
        principal.user,
        request_context(request),
    )
