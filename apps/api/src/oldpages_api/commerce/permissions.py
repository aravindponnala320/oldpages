from __future__ import annotations

from oldpages_api.commerce.exceptions import ForbiddenCommerceActionError
from oldpages_api.commerce.models import Offer, PickupSession, Transaction
from oldpages_api.identity.models import User


def require_offer_participant(actor: User, offer: Offer) -> None:
    if actor.id not in {offer.buyer_user_id, offer.seller_user_id}:
        raise ForbiddenCommerceActionError("Only offer participants can access this offer.")


def require_offer_recipient(actor: User, offer: Offer) -> None:
    require_offer_participant(actor, offer)
    if actor.id == offer.proposer_user_id:
        raise ForbiddenCommerceActionError("The offer proposer cannot perform this action.")


def require_offer_proposer(actor: User, offer: Offer) -> None:
    if actor.id != offer.proposer_user_id:
        raise ForbiddenCommerceActionError("Only the offer proposer can withdraw it.")


def require_transaction_participant(actor: User, transaction: Transaction) -> None:
    if actor.id not in {transaction.buyer_user_id, transaction.seller_user_id}:
        raise ForbiddenCommerceActionError(
            "Only transaction participants can access this transaction."
        )


def require_pickup_participant(actor: User, pickup: PickupSession) -> None:
    require_transaction_participant(actor, pickup.transaction)
