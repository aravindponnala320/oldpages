from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.commerce.events import (
    OFFER_ACCEPTED,
    OFFER_COUNTERED,
    OFFER_CREATED,
    OFFER_REJECTED,
    OFFER_WITHDRAWN,
    PICKUP_CONFIRMED,
    PICKUP_PROPOSED,
    REVIEW_CREATED,
    TRANSACTION_COMPLETED,
)
from oldpages_api.commerce.exceptions import (
    CommerceValidationError,
    InvalidCommerceStateTransitionError,
    OfferNotFoundError,
    PickupNotFoundError,
    TransactionNotFoundError,
)
from oldpages_api.commerce.models import (
    ExchangeOfferItem,
    Offer,
    PickupSession,
    Review,
    ReviewDimension,
    Transaction,
)
from oldpages_api.commerce.permissions import (
    require_offer_proposer,
    require_offer_recipient,
    require_pickup_participant,
    require_transaction_participant,
)
from oldpages_api.commerce.repository import CommerceRepository
from oldpages_api.commerce.schemas import (
    CommerceUserSummary,
    CounterOfferRequest,
    EmptyActionRequest,
    ExchangeOfferItemInput,
    ExchangeOfferItemResponse,
    FulfillmentMethod,
    OfferCreateRequest,
    OfferResponse,
    OfferStatus,
    OfferType,
    PickupConfirmRequest,
    PickupCreateRequest,
    PickupResponse,
    PickupStatus,
    ReviewCreateRequest,
    ReviewDimensionResponse,
    ReviewResponse,
    ReviewType,
    TransactionCompleteRequest,
    TransactionResponse,
    TransactionStatus,
)
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.listings.models import Listing
from oldpages_api.listings.tasks import refresh_listing_search_document

DEFAULT_OFFER_EXPIRY = timedelta(hours=48)


class CommerceService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CommerceRepository(session)

    async def create_offer(
        self,
        payload: OfferCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OfferResponse:
        listing = await self.get_listing_model(payload.listing_id)
        if listing.seller_user_id == actor.id:
            raise CommerceValidationError("Sellers cannot make offers on their own listings.")
        ensure_listing_accepts_offers(listing, payload.quantity, payload.fulfillment_method)
        expires_at = resolve_expires_at(payload.expires_at)
        offer = Offer(
            amount_cents=payload.amount_cents,
            bundle_listing_ids_json=list(payload.bundle_listing_ids),
            buyer_user_id=actor.id,
            currency=payload.currency,
            expires_at=expires_at,
            fulfillment_method=payload.fulfillment_method,
            listing_id=listing.id,
            message=payload.message,
            offer_type=payload.offer_type,
            proposer_user_id=actor.id,
            quantity=payload.quantity,
            seller_user_id=listing.seller_user_id,
            status="pending",
        )
        self.repo.add(offer)
        await self.repo.flush()
        await self.add_exchange_items(offer, payload.exchange_items, actor)
        await self.audit(
            action=OFFER_CREATED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id, "offer_id": offer.public_id},
            target_user_id=listing.seller_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_offer_model(offer.public_id)
        await self._broadcast_offer(reloaded, "offer.updated")
        return offer_response(reloaded)

    async def counter_offer(
        self,
        offer_id: str,
        payload: CounterOfferRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OfferResponse:
        offer = await self.get_offer_model(offer_id)
        require_offer_recipient(actor, offer)
        ensure_offer_pending(offer)
        ensure_not_expired(offer)
        expires_at = resolve_expires_at(payload.expires_at)
        offer.status = "countered"
        offer.responded_at = utc_now()
        counter = Offer(
            amount_cents=payload.amount_cents,
            bundle_listing_ids_json=list(offer.bundle_listing_ids_json),
            buyer_user_id=offer.buyer_user_id,
            currency=payload.currency,
            expires_at=expires_at,
            fulfillment_method=payload.fulfillment_method or offer.fulfillment_method,
            listing_id=offer.listing_id,
            message=payload.message,
            offer_type="counter",
            parent_offer_id=offer.id,
            proposer_user_id=actor.id,
            quantity=payload.quantity or offer.quantity,
            seller_user_id=offer.seller_user_id,
            status="pending",
        )
        ensure_listing_accepts_offers(offer.listing, counter.quantity, counter.fulfillment_method)
        self.repo.add(counter)
        await self.audit(
            action=OFFER_COUNTERED,
            actor=actor,
            context=context,
            payload={"offer_id": offer.public_id},
            target_user_id=other_offer_user_id(offer, actor.id),
        )
        await self.repo.commit()
        reloaded = await self.get_offer_model(counter.public_id)
        await self._broadcast_offer(reloaded, "offer.updated")
        # Also broadcast the parent (which is now "countered")
        parent_reloaded = await self.get_offer_model(offer.public_id)
        await self._broadcast_offer(parent_reloaded, "offer.updated")
        return offer_response(reloaded)

    async def accept_offer(
        self,
        offer_id: str,
        payload: EmptyActionRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OfferResponse:
        offer = await self.get_offer_model(offer_id)
        _ = payload
        require_offer_recipient(actor, offer)
        ensure_offer_pending(offer)
        ensure_not_expired(offer)
        ensure_listing_accepts_offers(offer.listing, offer.quantity, offer.fulfillment_method)
        reserved = await self.repo.reserve_inventory(offer.listing_id, offer.quantity)
        if not reserved:
            raise InvalidCommerceStateTransitionError("Listing inventory is no longer available.")
        await self.repo.flush()
        listing = await self.repo.get_listing_by_id(offer.listing_id)
        if listing is None:
            raise CommerceValidationError("Listing is no longer available.")
        if listing.inventory is not None and listing.inventory.quantity_available == 0:
            listing.status = "reserved"
        now = utc_now()
        offer.status = "accepted"
        offer.responded_at = now
        transaction = Transaction(
            amount_cents=offer.amount_cents,
            accepted_at=now,
            buyer_user_id=offer.buyer_user_id,
            currency=offer.currency,
            fulfillment_method=offer.fulfillment_method,
            listing_id=offer.listing_id,
            offer_id=offer.id,
            quantity=offer.quantity,
            seller_user_id=offer.seller_user_id,
            status="reserved",
        )
        self.repo.add(transaction)
        await self.audit(
            action=OFFER_ACCEPTED,
            actor=actor,
            context=context,
            payload={"offer_id": offer.public_id, "listing_id": offer.listing.public_id},
            target_user_id=other_offer_user_id(offer, actor.id),
        )
        await self.repo.commit()
        await refresh_listing_search_document(offer.listing_id)
        reloaded = await self.get_offer_model(offer.public_id)
        await self._broadcast_offer(reloaded, "offer.updated")
        return offer_response(reloaded)

    async def reject_offer(
        self,
        offer_id: str,
        payload: EmptyActionRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OfferResponse:
        offer = await self.get_offer_model(offer_id)
        require_offer_recipient(actor, offer)
        ensure_offer_pending(offer)
        expire_if_needed(offer)
        if offer.status == "expired":
            await self.repo.commit()
            raise InvalidCommerceStateTransitionError("Expired offers cannot be rejected.")
        offer.status = "rejected"
        offer.responded_at = utc_now()
        await self.audit(
            action=OFFER_REJECTED,
            actor=actor,
            context=context,
            payload={"offer_id": offer.public_id, "message": payload.message or ""},
            target_user_id=other_offer_user_id(offer, actor.id),
        )
        await self.repo.commit()
        reloaded = await self.get_offer_model(offer.public_id)
        await self._broadcast_offer(reloaded, "offer.updated")
        return offer_response(reloaded)

    async def withdraw_offer(
        self,
        offer_id: str,
        payload: EmptyActionRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OfferResponse:
        offer = await self.get_offer_model(offer_id)
        require_offer_proposer(actor, offer)
        ensure_offer_pending(offer)
        offer.status = "withdrawn"
        offer.responded_at = utc_now()
        await self.audit(
            action=OFFER_WITHDRAWN,
            actor=actor,
            context=context,
            payload={"offer_id": offer.public_id, "message": payload.message or ""},
            target_user_id=other_offer_user_id(offer, actor.id),
        )
        await self.repo.commit()
        reloaded = await self.get_offer_model(offer.public_id)
        await self._broadcast_offer(reloaded, "offer.updated")
        return offer_response(reloaded)

    async def create_pickup(
        self,
        payload: PickupCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> PickupResponse:
        transaction = await self.get_transaction_model(payload.transaction_id)
        require_transaction_participant(actor, transaction)
        if transaction.fulfillment_method != "pickup":
            raise CommerceValidationError("Only pickup transactions can have pickup sessions.")
        if transaction.status not in {"reserved", "ready_for_pickup"}:
            raise InvalidCommerceStateTransitionError(
                "Pickup can only be proposed for reserved transactions."
            )
        existing = await self.repo.get_pickup_for_transaction(transaction.id)
        if existing is not None and existing.status != "cancelled":
            return pickup_response(existing, actor)
        location = transaction.listing.location
        pickup = PickupSession(
            exact_address=payload.exact_address,
            exact_latitude=payload.exact_latitude
            or (location.exact_latitude if location else None),
            exact_longitude=payload.exact_longitude
            or (location.exact_longitude if location else None),
            handover_code=generate_handover_code(),
            pickup_notes_private=payload.pickup_notes_private
            or (location.pickup_notes_private if location else None),
            proposed_by_user_id=actor.id,
            proposed_end_at=payload.proposed_end_at,
            proposed_start_at=payload.proposed_start_at,
            public_location_label=payload.public_location_label
            or (location.public_area if location else "Pickup location"),
            status="proposed",
            transaction_id=transaction.id,
        )
        self.repo.add(pickup)
        await self.audit(
            action=PICKUP_PROPOSED,
            actor=actor,
            context=context,
            payload={"transaction_id": transaction.public_id},
            target_user_id=other_transaction_user_id(transaction, actor.id),
        )
        await self.repo.commit()
        reloaded = await self.get_pickup_model(pickup.public_id)
        return pickup_response(reloaded, actor)

    async def confirm_pickup(
        self,
        pickup_id: str,
        payload: PickupConfirmRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> PickupResponse:
        pickup = await self.get_pickup_model(pickup_id)
        _ = payload
        require_pickup_participant(actor, pickup)
        if pickup.proposed_by_user_id == actor.id:
            raise InvalidCommerceStateTransitionError(
                "Pickup proposals must be confirmed by the other participant."
            )
        if pickup.status != "proposed":
            raise InvalidCommerceStateTransitionError("Only proposed pickups can be confirmed.")
        pickup.status = "confirmed"
        pickup.confirmed_by_user_id = actor.id
        pickup.confirmed_at = utc_now()
        pickup.transaction.status = "ready_for_pickup"
        await self.audit(
            action=PICKUP_CONFIRMED,
            actor=actor,
            context=context,
            payload={"pickup_id": pickup.public_id},
            target_user_id=pickup.proposed_by_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_pickup_model(pickup.public_id)
        return pickup_response(reloaded, actor)

    async def complete_transaction(
        self,
        transaction_id: str,
        payload: TransactionCompleteRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> TransactionResponse:
        transaction = await self.get_transaction_model(transaction_id)
        require_transaction_participant(actor, transaction)
        if transaction.status not in {"reserved", "ready_for_pickup"}:
            raise InvalidCommerceStateTransitionError(
                "Only reserved transactions can be completed."
            )
        pickup = latest_pickup(transaction)
        if transaction.fulfillment_method == "pickup" and pickup is not None and pickup.status == "confirmed":
            if payload.handover_code != pickup.handover_code:
                raise CommerceValidationError("The handover code is incorrect.")
            pickup.status = "completed"
            pickup.completed_at = utc_now()
        transaction.status = "completed"
        transaction.completed_at = utc_now()
        if (
            transaction.listing.inventory is None
            or transaction.listing.inventory.quantity_available == 0
        ):
            transaction.listing.status = "completed"
        await self.audit(
            action=TRANSACTION_COMPLETED,
            actor=actor,
            context=context,
            payload={"transaction_id": transaction.public_id},
            target_user_id=other_transaction_user_id(transaction, actor.id),
        )
        await self.repo.commit()
        await refresh_listing_search_document(transaction.listing_id)
        reloaded = await self.get_transaction_model(transaction.public_id)
        return transaction_response(reloaded, actor)

    async def _broadcast_offer(self, offer: Offer, event_type: str) -> None:
        from oldpages_api.chat.tasks import publish_user_event
        resp = offer_response(offer)
        payload = {"offer_id": offer.public_id, "offer": resp.model_dump(mode="json")}
        for user in [offer.buyer, offer.seller]:
            if user and user.public_id:
                await publish_user_event(user.public_id, event_type, payload)

    async def _broadcast_txn(self, transaction: Transaction, actor: User, event_type: str) -> None:
        from oldpages_api.chat.tasks import publish_user_event
        resp = transaction_response(transaction, actor)
        payload = {"transaction_id": transaction.public_id, "transaction": resp.model_dump(mode="json")}
        # Broadcast to both parties
        for user in [transaction.buyer, transaction.seller]:
            if user and user.public_id:
                await publish_user_event(user.public_id, event_type, payload)

    async def cancel_transaction(
        self,
        transaction_id: str,
        reason: str | None,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> TransactionResponse:
        from oldpages_api.commerce.events import TRANSACTION_CANCELLED
        transaction = await self.get_transaction_model(transaction_id)
        require_transaction_participant(actor, transaction)
        if transaction.status in {"completed", "cancelled"}:
            raise InvalidCommerceStateTransitionError(
                f"Cannot cancel a {transaction.status} transaction."
            )
        transaction.status = "cancelled"
        transaction.cancelled_at = utc_now()
        transaction.cancelled_by_user_id = actor.id
        transaction.cancellation_reason = reason
        # Restore inventory
        if transaction.listing.inventory is not None:
            transaction.listing.inventory.quantity_available += transaction.quantity
            if transaction.listing.status == "reserved":
                transaction.listing.status = "active"
        # Cancel any active pickup sessions
        for pickup in transaction.pickup_sessions:
            if pickup.status in {"proposed", "confirmed"}:
                pickup.status = "cancelled"
        await self.audit(
            action=TRANSACTION_CANCELLED,
            actor=actor,
            context=context,
            payload={"transaction_id": transaction.public_id, "reason": reason or ""},
            target_user_id=other_transaction_user_id(transaction, actor.id),
        )
        await self.repo.commit()
        reloaded = await self.get_transaction_model(transaction.public_id)
        await self._broadcast_txn(reloaded, actor, "transaction.updated")
        return transaction_response(reloaded, actor)

    async def mark_transaction_received(
        self,
        transaction_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> TransactionResponse:
        """Buyer marks that they received the book. Auto-completes if seller also marked delivered."""
        from oldpages_api.commerce.events import TRANSACTION_MARKED_RECEIVED
        transaction = await self.get_transaction_model(transaction_id)
        if transaction.buyer_user_id != actor.id:
            from oldpages_api.commerce.exceptions import ForbiddenCommerceActionError
            raise ForbiddenCommerceActionError("Only the buyer can mark as received.")
        if transaction.status in {"completed", "cancelled"}:
            raise InvalidCommerceStateTransitionError(
                f"Cannot update a {transaction.status} transaction."
            )
        transaction.buyer_marked_received_at = utc_now()
        # Auto-complete if seller also confirmed
        if transaction.seller_marked_delivered_at is not None:
            transaction.status = "completed"
            transaction.completed_at = utc_now()
            if (
                transaction.listing.inventory is None
                or transaction.listing.inventory.quantity_available == 0
            ):
                transaction.listing.status = "completed"
        await self.audit(
            action=TRANSACTION_MARKED_RECEIVED,
            actor=actor,
            context=context,
            payload={"transaction_id": transaction.public_id},
            target_user_id=transaction.seller_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_transaction_model(transaction.public_id)
        await self._broadcast_txn(reloaded, actor, "transaction.updated")
        return transaction_response(reloaded, actor)

    async def mark_transaction_delivered(
        self,
        transaction_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> TransactionResponse:
        """Seller marks that they delivered the book. Auto-completes if buyer also marked received."""
        transaction = await self.get_transaction_model(transaction_id)
        if transaction.seller_user_id != actor.id:
            from oldpages_api.commerce.exceptions import ForbiddenCommerceActionError
            raise ForbiddenCommerceActionError("Only the seller can mark as delivered.")
        if transaction.status in {"completed", "cancelled"}:
            raise InvalidCommerceStateTransitionError(
                f"Cannot update a {transaction.status} transaction."
            )
        transaction.seller_marked_delivered_at = utc_now()
        # Auto-complete if buyer also confirmed
        if transaction.buyer_marked_received_at is not None:
            transaction.status = "completed"
            transaction.completed_at = utc_now()
            if (
                transaction.listing.inventory is None
                or transaction.listing.inventory.quantity_available == 0
            ):
                transaction.listing.status = "completed"
        await self.audit(
            action=TRANSACTION_COMPLETED,
            actor=actor,
            context=context,
            payload={"transaction_id": transaction.public_id},
            target_user_id=transaction.buyer_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_transaction_model(transaction.public_id)
        await self._broadcast_txn(reloaded, actor, "transaction.updated")
        return transaction_response(reloaded, actor)

    async def create_review(
        self,
        payload: ReviewCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReviewResponse:
        transaction = await self.get_transaction_model(payload.transaction_id)
        require_transaction_participant(actor, transaction)
        if transaction.status != "completed":
            raise InvalidCommerceStateTransitionError("Reviews require a completed transaction.")
        existing = await self.repo.get_review_for_reviewer(transaction.id, actor.id)
        if existing is not None:
            raise InvalidCommerceStateTransitionError(
                "Each participant can review a transaction once."
            )
        reviewee_user_id = other_transaction_user_id(transaction, actor.id)
        review_type: ReviewType = (
            "buyer_reviews_seller"
            if actor.id == transaction.buyer_user_id
            else "seller_reviews_buyer"
        )
        review = Review(
            comment=payload.comment,
            rating=payload.rating,
            review_type=review_type,
            reviewee_user_id=reviewee_user_id,
            reviewer_user_id=actor.id,
            status="published",
            transaction_id=transaction.id,
        )
        self.repo.add(review)
        await self.repo.flush()
        for item in payload.dimensions:
            self.repo.add(
                ReviewDimension(
                    dimension=item.dimension,
                    rating=item.rating,
                    review_id=review.id,
                )
            )
        await self.audit(
            action=REVIEW_CREATED,
            actor=actor,
            context=context,
            payload={"transaction_id": transaction.public_id, "review_id": review.public_id},
            target_user_id=reviewee_user_id,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_review_by_public_id(review.public_id)
        if reloaded is None:
            raise CommerceValidationError("Review could not be loaded.")
        return review_response(reloaded)

    async def add_exchange_items(
        self,
        offer: Offer,
        exchange_items: list[ExchangeOfferItemInput],
        actor: User,
    ) -> None:
        for item in exchange_items:
            offered_listing_id: int | None = None
            if item.offered_listing_id is not None:
                listing = await self.get_listing_model(item.offered_listing_id)
                if listing.seller_user_id != actor.id:
                    raise CommerceValidationError(
                        "Exchange offered listings must belong to the proposer."
                    )
                offered_listing_id = listing.id
            self.repo.add(
                ExchangeOfferItem(
                    cash_adjustment_cents=item.cash_adjustment_cents,
                    condition_note=item.condition_note,
                    offer_id=offer.id,
                    offered_listing_id=offered_listing_id,
                    title=item.title,
                )
            )

    async def list_offers(
        self,
        actor: User,
        role: str = "buyer",
        listing_id: str | None = None,
        limit: int = 50,
    ) -> list[OfferResponse]:
        listing_db_id: int | None = None
        if listing_id:
            listing = await self.repo.get_listing_by_public_id(listing_id)
            if listing:
                listing_db_id = listing.id
        offers = await self.repo.list_offers_for_user(actor.id, role=role, listing_id=listing_db_id, limit=limit)
        return [offer_response(o) for o in offers]

    async def list_transactions(
        self,
        actor: User,
        role: str = "buyer",
        limit: int = 50,
    ) -> list[TransactionResponse]:
        txns = await self.repo.list_transactions_for_user(actor.id, role=role, limit=limit)
        return [transaction_response(t, actor) for t in txns]

    async def get_offer(self, offer_id: str, actor: User) -> OfferResponse:
        offer = await self.get_offer_model(offer_id)
        if offer.buyer_user_id != actor.id and offer.seller_user_id != actor.id:
            from oldpages_api.commerce.exceptions import ForbiddenCommerceActionError
            raise ForbiddenCommerceActionError("You are not a party to this offer.")
        return offer_response(offer)

    async def get_transaction(self, transaction_id: str, actor: User) -> TransactionResponse:
        txn = await self.get_transaction_model(transaction_id)
        if txn.buyer_user_id != actor.id and txn.seller_user_id != actor.id:
            from oldpages_api.commerce.exceptions import ForbiddenCommerceActionError
            raise ForbiddenCommerceActionError("You are not a party to this transaction.")
        return transaction_response(txn, actor)

    async def get_listing_model(self, listing_id: str) -> Listing:
        listing = await self.repo.get_listing_by_public_id(listing_id)
        if listing is None:
            raise CommerceValidationError("Listing not found.")
        return listing

    async def get_offer_model(self, offer_id: str) -> Offer:
        offer = await self.repo.get_offer_by_public_id(offer_id)
        if offer is None:
            raise OfferNotFoundError()
        return offer

    async def get_transaction_model(self, transaction_id: str) -> Transaction:
        transaction = await self.repo.get_transaction_by_public_id(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError()
        return transaction

    async def get_pickup_model(self, pickup_id: str) -> PickupSession:
        pickup = await self.repo.get_pickup_by_public_id(pickup_id)
        if pickup is None:
            raise PickupNotFoundError()
        return pickup

    async def audit(
        self,
        *,
        action: str,
        actor: User,
        context: AuthenticatedRequestContext,
        payload: dict[str, str],
        target_user_id: int | None,
    ) -> None:
        self.repo.add(
            AuditLog(
                action=action,
                actor_user_id=actor.id,
                context_json=payload,
                ip_address=context.ip_address,
                target_user_id=target_user_id,
                user_agent=context.user_agent,
            )
        )


def ensure_listing_accepts_offers(
    listing: Listing,
    quantity: int,
    fulfillment_method: str,
) -> None:
    if listing.status != "active":
        raise InvalidCommerceStateTransitionError("Offers require an active listing.")
    if listing.inventory is None or listing.inventory.quantity_available < quantity:
        raise InvalidCommerceStateTransitionError("Listing inventory is not available.")
    if not any(
        method.method == fulfillment_method and method.enabled
        for method in listing.delivery_methods
    ):
        raise CommerceValidationError("The requested fulfillment method is not available.")


def ensure_offer_pending(offer: Offer) -> None:
    if offer.status != "pending":
        raise InvalidCommerceStateTransitionError("Only pending offers can be changed.")


def ensure_not_expired(offer: Offer) -> None:
    if as_utc(offer.expires_at) <= utc_now():
        offer.status = "expired"
        raise InvalidCommerceStateTransitionError("Expired offers cannot be accepted.")


def expire_if_needed(offer: Offer) -> None:
    if as_utc(offer.expires_at) <= utc_now():
        offer.status = "expired"


def resolve_expires_at(expires_at: datetime | None) -> datetime:
    resolved = as_utc(expires_at) if expires_at is not None else utc_now() + DEFAULT_OFFER_EXPIRY
    if resolved <= utc_now():
        raise CommerceValidationError("Offer expiration must be in the future.")
    return resolved


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def other_offer_user_id(offer: Offer, actor_user_id: int) -> int:
    return offer.seller_user_id if actor_user_id == offer.buyer_user_id else offer.buyer_user_id


def other_transaction_user_id(transaction: Transaction, actor_user_id: int) -> int:
    return (
        transaction.seller_user_id
        if actor_user_id == transaction.buyer_user_id
        else transaction.buyer_user_id
    )


def latest_pickup(transaction: Transaction) -> PickupSession | None:
    active = [pickup for pickup in transaction.pickup_sessions if pickup.status != "cancelled"]
    if not active:
        return None
    return sorted(active, key=lambda item: item.created_at)[-1]


def generate_handover_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


def can_view_exact_pickup(actor: User, transaction: Transaction) -> bool:
    return actor.id in {
        transaction.buyer_user_id,
        transaction.seller_user_id,
    } and transaction.status in {
        "reserved",
        "ready_for_pickup",
        "completed",
    }


def _user_summary(user: object) -> CommerceUserSummary:
    uid = getattr(user, "public_id", "")
    display_name: str | None = None
    try:
        from sqlalchemy import inspect as sa_inspect
        state = sa_inspect(user)
        # Only access .profile if already loaded (not deferred/unloaded)
        if "profile" not in state.unloaded:
            profile = user.profile  # type: ignore[attr-defined]
            if profile is not None:
                display_name = getattr(profile, "display_name", None)
    except Exception:
        pass
    return CommerceUserSummary(id=uid, display_name=display_name)


def offer_response(offer: Offer) -> OfferResponse:
    listing_title = getattr(offer.listing, "title_snapshot", None)
    listing_price = getattr(offer.listing, "price_amount_cents", None)
    return OfferResponse(
        amount_cents=offer.amount_cents,
        bundle_listing_ids=list(offer.bundle_listing_ids_json),
        buyer=_user_summary(offer.buyer),
        created_at=offer.created_at,
        currency=offer.currency,
        exchange_items=[
            ExchangeOfferItemResponse(
                cash_adjustment_cents=item.cash_adjustment_cents,
                condition_note=item.condition_note,
                id=item.public_id,
                offered_listing_id=item.offered_listing.public_id if item.offered_listing else None,
                title=item.title,
            )
            for item in offer.exchange_items
        ],
        expires_at=offer.expires_at,
        fulfillment_method=cast("FulfillmentMethod", offer.fulfillment_method),
        id=offer.public_id,
        listing_id=offer.listing.public_id,
        listing_title=listing_title,
        listing_price_cents=listing_price,
        message=offer.message,
        offer_type=cast("OfferType", offer.offer_type),
        parent_offer_id=offer.parent.public_id if offer.parent else None,
        proposer=_user_summary(offer.proposer),
        quantity=offer.quantity,
        responded_at=offer.responded_at,
        seller=_user_summary(offer.seller),
        status=cast("OfferStatus", offer.status),
        transaction_id=offer.transaction.public_id if offer.transaction else None,
    )


def pickup_response(pickup: PickupSession, actor: User) -> PickupResponse:
    include_exact = can_view_exact_pickup(actor, pickup.transaction)
    return PickupResponse(
        confirmed_at=pickup.confirmed_at,
        confirmed_by_user_id=pickup.confirmed_by.public_id if pickup.confirmed_by else None,
        exact_address=pickup.exact_address if include_exact else None,
        exact_latitude=pickup.exact_latitude if include_exact else None,
        exact_longitude=pickup.exact_longitude if include_exact else None,
        handover_code=pickup.handover_code if include_exact else None,
        id=pickup.public_id,
        pickup_notes_private=pickup.pickup_notes_private if include_exact else None,
        proposed_by_user_id=pickup.proposed_by.public_id,
        proposed_end_at=pickup.proposed_end_at,
        proposed_start_at=pickup.proposed_start_at,
        public_location_label=pickup.public_location_label,
        status=cast("PickupStatus", pickup.status),
        transaction_id=pickup.transaction.public_id,
    )


def transaction_response(transaction: Transaction, actor: User) -> TransactionResponse:
    pickup = latest_pickup(transaction)
    cancelled_by_public = None
    if getattr(transaction, "cancelled_by_user_id", None):
        # Find via buyer/seller relationships
        if transaction.buyer and transaction.buyer.id == transaction.cancelled_by_user_id:
            cancelled_by_public = transaction.buyer.public_id
        elif transaction.seller and transaction.seller.id == transaction.cancelled_by_user_id:
            cancelled_by_public = transaction.seller.public_id
    return TransactionResponse(
        amount_cents=transaction.amount_cents,
        buyer=_user_summary(transaction.buyer),
        completed_at=transaction.completed_at,
        created_at=transaction.created_at,
        currency=transaction.currency,
        fulfillment_method=cast("FulfillmentMethod", transaction.fulfillment_method),
        id=transaction.public_id,
        listing_id=transaction.listing.public_id,
        offer_id=transaction.offer.public_id,
        pickup=pickup_response(pickup, actor) if pickup else None,
        quantity=transaction.quantity,
        seller=_user_summary(transaction.seller),
        status=cast("TransactionStatus", transaction.status),
        cancellation_reason=getattr(transaction, "cancellation_reason", None),
        cancelled_at=getattr(transaction, "cancelled_at", None),
        cancelled_by_user_id=cancelled_by_public,
        buyer_marked_received_at=getattr(transaction, "buyer_marked_received_at", None),
        seller_marked_delivered_at=getattr(transaction, "seller_marked_delivered_at", None),
    )


def review_response(review: Review) -> ReviewResponse:
    return ReviewResponse(
        comment=review.comment,
        created_at=review.created_at,
        dimensions=[
            ReviewDimensionResponse(
                dimension=dimension.dimension,
                id=dimension.public_id,
                rating=dimension.rating,
            )
            for dimension in sorted(review.dimensions, key=lambda item: item.dimension)
        ],
        id=review.public_id,
        rating=review.rating,
        review_type=cast("ReviewType", review.review_type),
        reviewee=CommerceUserSummary(id=review.reviewee.public_id),
        reviewer=CommerceUserSummary(id=review.reviewer.public_id),
        status=review.status,
        transaction_id=review.transaction.public_id,
    )
