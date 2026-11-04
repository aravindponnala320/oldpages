from __future__ import annotations

from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.donations.events import (
    CAMPAIGN_CREATED,
    DONATION_PLEDGED,
    DONATION_RECEIVED,
    RECEIPT_ISSUED,
)
from oldpages_api.donations.exceptions import (
    CampaignNotFoundError,
    DonationValidationError,
    PledgeNotFoundError,
)
from oldpages_api.donations.models import (
    DonationCampaign,
    DonationNeed,
    DonationPledge,
    DonationReceipt,
)
from oldpages_api.donations.permissions import require_campaign_owner, require_pledge_donor
from oldpages_api.donations.repository import DonationRepository
from oldpages_api.donations.schemas import (
    CampaignCreateRequest,
    CampaignImpactResponse,
    CampaignListResponse,
    CampaignResponse,
    CampaignStatus,
    CampaignUpdateRequest,
    DonationNeedImpactResponse,
    DonationNeedResponse,
    DonationReceiptResponse,
    PledgeDonationRequest,
    PledgeResponse,
    PledgeStatus,
    ReceiptIssueRequest,
)
from oldpages_api.identity.models import User
from oldpages_api.identity.security import utc_now


class DonationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = DonationRepository(session)

    async def create_campaign(
        self,
        payload: CampaignCreateRequest,
        actor: User,
    ) -> CampaignResponse:
        institution_id: int | None = None
        if payload.institution_id is not None:
            from sqlalchemy import select

            from oldpages_api.institutions.models import Institution

            result = await self.repo.session.execute(
                select(Institution).where(Institution.public_id == payload.institution_id)
            )
            inst = result.scalar_one_or_none()
            if inst is None:
                raise DonationValidationError("Institution not found.")
            institution_id = inst.id

        campaign = DonationCampaign(
            accepted_conditions_json=list(payload.accepted_conditions),
            city=payload.city,
            country="IN",
            created_by_user_id=actor.id,
            deadline_at=payload.deadline_at,
            description=payload.description,
            dropoff_address=payload.dropoff_address,
            institution_id=institution_id,
            is_public=payload.is_public,
            pickup_address=payload.pickup_address,
            quantity_pledged=0,
            quantity_received=0,
            quantity_target=payload.quantity_target,
            state=payload.state,
            status="draft",
            title=payload.title,
        )
        self.repo.add(campaign)
        await self.repo.flush()
        for need_input in payload.needs:
            need = DonationNeed(
                author=need_input.author,
                campaign_id=campaign.id,
                quantity_needed=need_input.quantity_needed,
                quantity_pledged=0,
                title=need_input.title,
            )
            self.repo.add(need)
        await self.repo.commit()
        reloaded = await self.repo.get_campaign_by_id(campaign.id)
        if reloaded is None:
            raise DonationValidationError("Campaign could not be loaded.")
        _ = CAMPAIGN_CREATED
        return campaign_response(reloaded)

    async def publish_campaign(self, campaign_id: str, actor: User) -> CampaignResponse:
        campaign = await self.get_campaign_model(campaign_id)
        require_campaign_owner(campaign, actor)
        if campaign.status not in {"draft", "paused"}:
            raise DonationValidationError("Only draft or paused campaigns can be published.")
        campaign.status = "active"
        await self.repo.commit()
        reloaded = await self.repo.get_campaign_by_id(campaign.id)
        if reloaded is None:
            raise DonationValidationError("Campaign could not be loaded.")
        return campaign_response(reloaded)

    async def get_campaign(self, campaign_id: str) -> CampaignResponse:
        campaign = await self.repo.get_campaign_by_public_id(campaign_id)
        if campaign is None:
            raise CampaignNotFoundError()
        return campaign_response(campaign)

    async def get_campaign_impact(self, campaign_id: str) -> CampaignImpactResponse:
        campaign = await self.repo.get_campaign_by_public_id(campaign_id)
        if campaign is None:
            raise CampaignNotFoundError()
        return campaign_impact_response(campaign)

    async def list_campaigns(
        self,
        filters: dict[str, str | None],
        limit: int = 20,
        cursor: str | None = None,
    ) -> CampaignListResponse:
        campaigns = await self.repo.list_campaigns(filters, limit=limit, cursor=cursor)
        next_cursor = campaigns[-1].public_id if len(campaigns) == limit else None
        return CampaignListResponse(
            items=[campaign_response(c) for c in campaigns],
            next_cursor=next_cursor,
        )

    async def update_campaign(
        self,
        campaign_id: str,
        payload: CampaignUpdateRequest,
        actor: User,
    ) -> CampaignResponse:
        campaign = await self.get_campaign_model(campaign_id)
        require_campaign_owner(campaign, actor)
        if payload.title is not None:
            campaign.title = payload.title
        if payload.description is not None:
            campaign.description = payload.description
        if payload.accepted_conditions is not None:
            campaign.accepted_conditions_json = list(payload.accepted_conditions)
        if payload.pickup_address is not None:
            campaign.pickup_address = payload.pickup_address
        if payload.dropoff_address is not None:
            campaign.dropoff_address = payload.dropoff_address
        if payload.deadline_at is not None:
            campaign.deadline_at = payload.deadline_at
        if payload.is_public is not None:
            campaign.is_public = payload.is_public
        if payload.city is not None:
            campaign.city = payload.city
        if payload.state is not None:
            campaign.state = payload.state
        await self.repo.commit()
        reloaded = await self.repo.get_campaign_by_id(campaign.id)
        if reloaded is None:
            raise DonationValidationError("Campaign could not be loaded.")
        return campaign_response(reloaded)

    async def pledge_donation(
        self,
        campaign_id: str,
        payload: PledgeDonationRequest,
        actor: User,
    ) -> PledgeResponse:
        campaign = await self.get_campaign_model(campaign_id)
        if campaign.status != "active":
            raise DonationValidationError("Donations can only be pledged to active campaigns.")
        accepted_conditions = {
            condition.strip().lower()
            for condition in campaign.accepted_conditions_json
            if condition.strip()
        }
        if accepted_conditions and payload.condition.strip().lower() not in accepted_conditions:
            raise DonationValidationError("Pledge condition is not accepted for this campaign.")

        donation_need_id: int | None = None
        if payload.donation_need_id is not None:
            need = await self.repo.get_need_by_public_id(payload.donation_need_id)
            if need is None or need.campaign_id != campaign.id:
                raise DonationValidationError("Donation need not found for this campaign.")
            donation_need_id = need.id
            need.quantity_pledged = need.quantity_pledged + payload.quantity

        pledge = DonationPledge(
            campaign_id=campaign.id,
            condition=payload.condition,
            donation_need_id=donation_need_id,
            donor_user_id=actor.id,
            notes=payload.notes,
            quantity=payload.quantity,
            status="pending",
            title_snapshot=payload.title_snapshot,
        )
        campaign.quantity_pledged = campaign.quantity_pledged + payload.quantity
        self.repo.add(pledge)
        await self.repo.commit()
        reloaded = await self.repo.get_pledge_by_public_id(pledge.public_id)
        if reloaded is None:
            raise DonationValidationError("Pledge could not be loaded.")
        _ = DONATION_PLEDGED
        return pledge_response(reloaded)

    async def accept_pledge(
        self,
        campaign_id: str,
        pledge_id: str,
        actor: User,
    ) -> PledgeResponse:
        campaign = await self.get_campaign_model(campaign_id)
        require_campaign_owner(campaign, actor)
        pledge = await self.repo.get_pledge_by_public_id(pledge_id)
        if pledge is None or pledge.campaign_id != campaign.id:
            raise PledgeNotFoundError()
        if pledge.status != "pending":
            raise DonationValidationError("Only pending pledges can be accepted.")
        pledge.status = "accepted"
        pledge.accepted_at = utc_now()
        await self.repo.commit()
        reloaded = await self.repo.get_pledge_by_public_id(pledge.public_id)
        if reloaded is None:
            raise PledgeNotFoundError()
        return pledge_response(reloaded)

    async def mark_received(
        self,
        campaign_id: str,
        pledge_id: str,
        actor: User,
    ) -> PledgeResponse:
        campaign = await self.get_campaign_model(campaign_id)
        require_campaign_owner(campaign, actor)
        pledge = await self.repo.get_pledge_by_public_id(pledge_id)
        if pledge is None or pledge.campaign_id != campaign.id:
            raise PledgeNotFoundError()
        if pledge.status not in {"accepted", "pickup_scheduled"}:
            raise DonationValidationError(
                "Only accepted or pickup-scheduled pledges can be marked received."
            )
        pledge.status = "received"
        pledge.received_at = utc_now()
        campaign.quantity_received = campaign.quantity_received + pledge.quantity
        await self.repo.commit()
        _ = DONATION_RECEIVED
        reloaded = await self.repo.get_pledge_by_public_id(pledge.public_id)
        if reloaded is None:
            raise PledgeNotFoundError()
        return pledge_response(reloaded)

    async def issue_receipt(
        self,
        campaign_id: str,
        pledge_id: str,
        payload: ReceiptIssueRequest,
        actor: User,
    ) -> PledgeResponse:
        campaign = await self.get_campaign_model(campaign_id)
        require_campaign_owner(campaign, actor)
        pledge = await self.repo.get_pledge_by_public_id(pledge_id)
        if pledge is None or pledge.campaign_id != campaign.id:
            raise PledgeNotFoundError()
        if pledge.status != "received":
            raise DonationValidationError("Receipts can only be issued for received pledges.")
        existing = await self.repo.get_receipt_by_pledge_id(pledge.id)
        if existing is not None:
            raise DonationValidationError("A receipt has already been issued for this pledge.")
        receipt = DonationReceipt(
            campaign_id=campaign.id,
            impact_note=payload.impact_note,
            issued_at=utc_now(),
            issued_by_user_id=actor.id,
            pledge_id=pledge.id,
            receipt_text=payload.receipt_text,
        )
        self.repo.add(receipt)
        await self.repo.commit()
        _ = RECEIPT_ISSUED
        reloaded = await self.repo.get_pledge_by_public_id(pledge.public_id)
        if reloaded is None:
            raise PledgeNotFoundError()
        return pledge_response(reloaded)

    async def get_pledge(self, pledge_id: str, actor: User) -> PledgeResponse:
        pledge = await self.repo.get_pledge_by_public_id(pledge_id)
        if pledge is None:
            raise PledgeNotFoundError()
        require_pledge_donor(pledge, actor)
        return pledge_response(pledge)

    async def list_campaign_pledges(
        self,
        campaign_id: str,
        actor: User,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[PledgeResponse]:
        campaign = await self.get_campaign_model(campaign_id)
        require_campaign_owner(campaign, actor)
        pledges = await self.repo.list_pledges(campaign.id, limit=limit, cursor=cursor)
        return [pledge_response(p) for p in pledges]

    async def list_my_pledges(
        self,
        actor: User,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[PledgeResponse]:
        pledges = await self.repo.list_my_pledges(actor.id, limit=limit, cursor=cursor)
        return [pledge_response(p) for p in pledges]

    async def get_campaign_model(self, campaign_id: str) -> DonationCampaign:
        campaign = await self.repo.get_campaign_by_public_id(campaign_id)
        if campaign is None:
            raise CampaignNotFoundError()
        return campaign


def need_response(need: DonationNeed, campaign: DonationCampaign) -> DonationNeedResponse:
    return DonationNeedResponse(
        author=need.author,
        book_id=None,
        campaign_id=campaign.public_id,
        created_at=need.created_at,
        id=need.public_id,
        quantity_needed=need.quantity_needed,
        quantity_pledged=need.quantity_pledged,
        title=need.title,
    )


def campaign_response(campaign: DonationCampaign) -> CampaignResponse:
    return CampaignResponse(
        accepted_conditions=list(campaign.accepted_conditions_json),
        city=campaign.city,
        country=campaign.country,
        created_at=campaign.created_at,
        created_by_user_id=campaign.created_by.public_id,
        deadline_at=campaign.deadline_at,
        description=campaign.description,
        dropoff_address=campaign.dropoff_address,
        id=campaign.public_id,
        institution_id=None,
        is_public=campaign.is_public,
        needs=[need_response(n, campaign) for n in campaign.needs],
        pickup_address=campaign.pickup_address,
        quantity_pledged=campaign.quantity_pledged,
        quantity_received=campaign.quantity_received,
        quantity_target=campaign.quantity_target,
        state=campaign.state,
        status=cast("CampaignStatus", campaign.status),
        title=campaign.title,
        updated_at=campaign.updated_at,
    )


def campaign_impact_response(campaign: DonationCampaign) -> CampaignImpactResponse:
    return CampaignImpactResponse(
        campaign_id=campaign.public_id,
        needs=[
            DonationNeedImpactResponse(
                need_id=need.public_id,
                quantity_needed=need.quantity_needed,
                quantity_pledged=need.quantity_pledged,
                title=need.title,
            )
            for need in campaign.needs
        ],
        pledge_count=len(campaign.pledges),
        quantity_pledged=campaign.quantity_pledged,
        quantity_received=campaign.quantity_received,
        quantity_target=campaign.quantity_target,
        receipt_count=sum(1 for pledge in campaign.pledges if pledge.receipt is not None),
        received_pledge_count=sum(1 for pledge in campaign.pledges if pledge.status == "received"),
    )


def receipt_response(receipt: DonationReceipt) -> DonationReceiptResponse:
    return DonationReceiptResponse(
        campaign_id=receipt.campaign.public_id if receipt.campaign else "",
        created_at=receipt.created_at,
        id=receipt.public_id,
        impact_note=receipt.impact_note,
        issued_at=receipt.issued_at,
        issued_by_user_id=receipt.issued_by.public_id,
        pledge_id=receipt.pledge.public_id if receipt.pledge else "",
        receipt_text=receipt.receipt_text,
    )


def pledge_response(pledge: DonationPledge) -> PledgeResponse:
    return PledgeResponse(
        accepted_at=pledge.accepted_at,
        campaign_id=pledge.campaign.public_id,
        condition=pledge.condition,
        created_at=pledge.created_at,
        donation_need_id=pledge.donation_need.public_id if pledge.donation_need else None,
        donor_user_id=pledge.donor.public_id,
        id=pledge.public_id,
        notes=pledge.notes,
        quantity=pledge.quantity,
        receipt=receipt_response(pledge.receipt) if pledge.receipt else None,
        received_at=pledge.received_at,
        status=cast("PledgeStatus", pledge.status),
        title_snapshot=pledge.title_snapshot,
        updated_at=pledge.updated_at,
    )
