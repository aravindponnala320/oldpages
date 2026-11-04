from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.donations.schemas import (
    CampaignCreateRequest,
    CampaignImpactResponse,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdateRequest,
    PledgeDonationRequest,
    PledgeResponse,
    ReceiptIssueRequest,
)
from oldpages_api.donations.service import DonationService
from oldpages_api.identity.dependencies import CurrentPrincipal, get_current_principal
from oldpages_api.shared.db.database import get_session

campaigns_router = APIRouter(prefix="/donations/campaigns", tags=["donations"])
donations_router = APIRouter(prefix="/donations", tags=["donations"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def donation_service(session: AsyncSession) -> DonationService:
    return DonationService(session)


@campaigns_router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> CampaignResponse:
    return await donation_service(session).create_campaign(payload, principal.user)


@campaigns_router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    session: SessionDep,
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    institution_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> CampaignListResponse:
    filters = {"city": city, "state": state, "institution_id": institution_id}
    return await donation_service(session).list_campaigns(filters, limit=limit, cursor=cursor)


@campaigns_router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    session: SessionDep,
) -> CampaignResponse:
    return await donation_service(session).get_campaign(campaign_id)


@campaigns_router.get("/{campaign_id}/impact", response_model=CampaignImpactResponse)
async def get_campaign_impact(
    campaign_id: str,
    session: SessionDep,
) -> CampaignImpactResponse:
    return await donation_service(session).get_campaign_impact(campaign_id)


@campaigns_router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    payload: CampaignUpdateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> CampaignResponse:
    return await donation_service(session).update_campaign(campaign_id, payload, principal.user)


@campaigns_router.post("/{campaign_id}/publish", response_model=CampaignResponse)
async def publish_campaign(
    campaign_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> CampaignResponse:
    return await donation_service(session).publish_campaign(campaign_id, principal.user)


@campaigns_router.post(
    "/{campaign_id}/pledge",
    response_model=PledgeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def pledge_donation(
    campaign_id: str,
    payload: PledgeDonationRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> PledgeResponse:
    return await donation_service(session).pledge_donation(campaign_id, payload, principal.user)


@campaigns_router.get("/{campaign_id}/pledges", response_model=list[PledgeResponse])
async def list_pledges(
    campaign_id: str,
    principal: PrincipalDep,
    session: SessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> list[PledgeResponse]:
    return await donation_service(session).list_campaign_pledges(
        campaign_id, principal.user, limit=limit, cursor=cursor
    )


@campaigns_router.post(
    "/{campaign_id}/pledges/{pledge_id}/accept",
    response_model=PledgeResponse,
)
async def accept_pledge(
    campaign_id: str,
    pledge_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> PledgeResponse:
    return await donation_service(session).accept_pledge(campaign_id, pledge_id, principal.user)


@campaigns_router.post(
    "/{campaign_id}/pledges/{pledge_id}/received",
    response_model=PledgeResponse,
)
async def mark_received(
    campaign_id: str,
    pledge_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> PledgeResponse:
    return await donation_service(session).mark_received(campaign_id, pledge_id, principal.user)


@campaigns_router.post(
    "/{campaign_id}/pledges/{pledge_id}/receipt",
    response_model=PledgeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_receipt(
    campaign_id: str,
    pledge_id: str,
    payload: ReceiptIssueRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> PledgeResponse:
    return await donation_service(session).issue_receipt(
        campaign_id, pledge_id, payload, principal.user
    )


@donations_router.get("/pledges/me", response_model=list[PledgeResponse])
async def list_my_pledges(
    principal: PrincipalDep,
    session: SessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> list[PledgeResponse]:
    return await donation_service(session).list_my_pledges(
        principal.user, limit=limit, cursor=cursor
    )
