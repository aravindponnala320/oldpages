from __future__ import annotations

from oldpages_api.donations.exceptions import ForbiddenDonationActionError
from oldpages_api.donations.models import DonationCampaign, DonationPledge
from oldpages_api.identity.models import User


def require_campaign_owner(campaign: DonationCampaign, user: User) -> None:
    if campaign.created_by_user_id != user.id:
        raise ForbiddenDonationActionError("Only the campaign owner can perform this action.")


def require_pledge_donor(pledge: DonationPledge, user: User) -> None:
    if pledge.donor_user_id != user.id:
        raise ForbiddenDonationActionError("Only the pledge donor can access this pledge.")
