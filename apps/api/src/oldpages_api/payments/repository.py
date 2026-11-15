from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.commerce.models import PickupSession, Transaction
from oldpages_api.identity.models import UserPreference
from oldpages_api.listings.models import Listing, ListingInventory
from oldpages_api.payments.models import (
    Cart,
    CartItem,
    Dispute,
    IdempotencyKey,
    Order,
    Payment,
    Payout,
    Refund,
    Shipment,
    WebhookEvent,
)


class PaymentsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Cart ---

    async def get_cart_by_public_id(self, public_id: str) -> Cart | None:
        result = await self.session.execute(
            select(Cart)
            .execution_options(populate_existing=True)
            .options(*cart_load_options())
            .where(Cart.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_active_cart_for_buyer_seller(
        self,
        buyer_user_id: int,
        seller_user_id: int,
    ) -> Cart | None:
        result = await self.session.execute(
            select(Cart)
            .execution_options(populate_existing=True)
            .options(*cart_load_options())
            .where(
                Cart.buyer_user_id == buyer_user_id,
                Cart.seller_user_id == seller_user_id,
                Cart.status == "active",
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_cart_item_by_public_id(self, public_id: str) -> CartItem | None:
        result = await self.session.execute(select(CartItem).where(CartItem.public_id == public_id))
        return result.scalar_one_or_none()

    # --- Order ---

    async def get_order_by_public_id(self, public_id: str) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .execution_options(populate_existing=True)
            .options(*order_load_options())
            .where(Order.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_orders_for_user(
        self,
        user_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .execution_options(populate_existing=True)
            .options(*order_load_options())
            .where((Order.buyer_user_id == user_id) | (Order.seller_user_id == user_id))
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.unique().scalars().all())

    # --- Payment ---

    async def get_payment_by_public_id(self, public_id: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment)
            .execution_options(populate_existing=True)
            .options(selectinload(Payment.order), selectinload(Payment.refunds))
            .where(Payment.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_payment_by_idempotency_key(
        self,
        idempotency_key: str,
        order_id: int,
    ) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(
                Payment.idempotency_key == idempotency_key,
                Payment.order_id == order_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_payment_by_provider_payment_id(
        self,
        provider: str,
        provider_payment_id: str,
    ) -> Payment | None:
        result = await self.session.execute(
            select(Payment)
            .execution_options(populate_existing=True)
            .options(selectinload(Payment.order), selectinload(Payment.refunds))
            .where(
                Payment.provider == provider,
                Payment.provider_payment_id == provider_payment_id,
            )
        )
        return result.unique().scalar_one_or_none()

    # --- Payout ---

    async def get_payout_by_public_id(self, public_id: str) -> Payout | None:
        result = await self.session.execute(
            select(Payout)
            .execution_options(populate_existing=True)
            .options(selectinload(Payout.order), selectinload(Payout.seller))
            .where(Payout.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    # --- Refund ---

    async def get_refund_by_public_id(self, public_id: str) -> Refund | None:
        result = await self.session.execute(
            select(Refund)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Refund.order),
                selectinload(Refund.payment),
            )
            .where(Refund.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    # --- Shipment ---

    async def get_shipment_by_public_id(self, public_id: str) -> Shipment | None:
        result = await self.session.execute(
            select(Shipment)
            .execution_options(populate_existing=True)
            .options(selectinload(Shipment.order))
            .where(Shipment.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_shipment_by_provider_id(self, provider_shipment_id: str) -> Shipment | None:
        result = await self.session.execute(
            select(Shipment)
            .execution_options(populate_existing=True)
            .options(selectinload(Shipment.order))
            .where(Shipment.provider_shipment_id == provider_shipment_id)
        )
        return result.unique().scalar_one_or_none()

    # --- Dispute ---

    async def get_dispute_by_public_id(self, public_id: str) -> Dispute | None:
        result = await self.session.execute(
            select(Dispute)
            .execution_options(populate_existing=True)
            .options(*dispute_load_options())
            .where(Dispute.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    # --- WebhookEvent ---

    async def get_webhook_event_by_provider_event_id(
        self,
        provider: str,
        provider_event_id: str,
    ) -> WebhookEvent | None:
        result = await self.session.execute(
            select(WebhookEvent).where(
                WebhookEvent.provider == provider,
                WebhookEvent.provider_event_id == provider_event_id,
            )
        )
        return result.scalar_one_or_none()

    # --- IdempotencyKey ---

    async def get_idempotency_key(self, key: str) -> IdempotencyKey | None:
        result = await self.session.execute(select(IdempotencyKey).where(IdempotencyKey.key == key))
        return result.scalar_one_or_none()

    async def get_order_for_cart(self, cart_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).options(*order_load_options()).where(Order.cart_id == cart_id)
        )
        return result.scalar_one_or_none()

    async def get_order_for_offer(self, offer_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).options(*order_load_options()).where(Order.offer_id == offer_id)
        )
        return result.scalar_one_or_none()

    # --- Stock ---

    async def claim_active_cart(self, cart_id: int) -> bool:
        """Moves the cart out of 'active' once, so two checkouts can't both proceed."""
        result = await self.session.execute(
            update(Cart)
            .where(Cart.id == cart_id, Cart.status == "active")
            .values(status="checked_out")
            .execution_options(synchronize_session=False)
        )
        return cast("CursorResult[Any]", result).rowcount == 1

    async def get_listings_for_checkout(self, listing_ids: list[int]) -> dict[int, Listing]:
        result = await self.session.execute(
            select(Listing)
            .options(
                selectinload(Listing.condition),
                selectinload(Listing.delivery_methods),
                selectinload(Listing.inventory),
            )
            .where(Listing.id.in_(listing_ids))
        )
        return {listing.id: listing for listing in result.scalars().all()}

    async def reserve_inventory(self, listing_id: int, quantity: int) -> bool:
        result = await self.session.execute(
            update(ListingInventory)
            .where(
                ListingInventory.listing_id == listing_id,
                ListingInventory.quantity_available >= quantity,
            )
            .values(quantity_available=ListingInventory.quantity_available - quantity)
            .execution_options(synchronize_session=False)
        )
        return cast("CursorResult[Any]", result).rowcount == 1

    async def release_inventory(self, listing_id: int, quantity: int) -> None:
        await self.session.execute(
            update(ListingInventory)
            .where(
                ListingInventory.listing_id == listing_id,
                ListingInventory.quantity_available + quantity <= ListingInventory.quantity_total,
            )
            .values(quantity_available=ListingInventory.quantity_available + quantity)
            .execution_options(synchronize_session=False)
        )
        await self.session.execute(
            update(Listing)
            .where(Listing.id == listing_id, Listing.status == "reserved")
            .values(status="active")
            .execution_options(synchronize_session=False)
        )

    async def get_open_transaction_for_offer(self, offer_id: int) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.offer_id == offer_id,
                Transaction.status.in_(("reserved", "ready_for_pickup")),
            )
        )
        return result.scalar_one_or_none()

    # --- Background jobs ---

    async def unpaid_orders_before(self, cutoff: datetime, limit: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(*order_load_options())
            .where(Order.status == "awaiting_payment", Order.created_at < cutoff)
            .order_by(Order.id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delivered_orders_before(self, cutoff: datetime, limit: int) -> list[Order]:
        delivered_long_ago = exists().where(
            Shipment.order_id == Order.id,
            Shipment.status == "delivered",
            Shipment.delivered_at < cutoff,
        )
        open_dispute = exists().where(
            Dispute.order_id == Order.id, Dispute.status.in_(("opened", "under_review"))
        )
        result = await self.session.execute(
            select(Order)
            .options(*order_load_options())
            .where(Order.status == "delivered", delivered_long_ago, ~open_dispute)
            .order_by(Order.id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def stale_offer_holds(self, cutoff: datetime, limit: int) -> list[Transaction]:
        """Accepted offers still holding a copy with no pickup planned and no order paid."""
        planned_pickup = exists().where(
            PickupSession.transaction_id == Transaction.id,
            PickupSession.status.in_(("proposed", "confirmed")),
        )
        paying_order = exists().where(
            Order.offer_id == Transaction.offer_id,
            Order.status.notin_(("created", "awaiting_payment", "cancelled")),
        )
        result = await self.session.execute(
            select(Transaction)
            .where(
                Transaction.status == "reserved",
                Transaction.accepted_at < cutoff,
                ~planned_pickup,
                ~paying_order,
            )
            .order_by(Transaction.id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def complete_listing_if_sold_out(self, listing_id: int) -> None:
        sold_out = exists().where(
            ListingInventory.listing_id == listing_id, ListingInventory.quantity_available == 0
        )
        await self.session.execute(
            update(Listing)
            .where(Listing.id == listing_id, Listing.status == "reserved", sold_out)
            .values(status="completed")
            .execution_options(synchronize_session=False)
        )

    async def cancel_unpaid_offer_orders(self, offer_id: int) -> None:
        await self.session.execute(
            update(Order)
            .where(Order.offer_id == offer_id, Order.status.in_(("created", "awaiting_payment")))
            .values(status="cancelled")
            .execution_options(synchronize_session=False)
        )

    async def move_order_status(self, order_id: int, from_status: str, to_status: str) -> bool:
        """Changes status only if nothing else changed it first (e.g. a payment landing)."""
        result = await self.session.execute(
            update(Order)
            .where(Order.id == order_id, Order.status == from_status)
            .values(status=to_status)
            .execution_options(synchronize_session=False)
        )
        return cast("CursorResult[Any]", result).rowcount == 1

    # --- Session helpers ---

    async def user_has_any_role(self, user_id: int, roles: tuple[str, ...]) -> bool:
        # Roles live in user preferences (see trust.repository.user_has_role).
        result = await self.session.execute(
            select(UserPreference.metadata_json).where(UserPreference.user_id == user_id)
        )
        metadata: dict[str, Any] = result.scalar_one_or_none() or {}
        granted = metadata.get("roles", [])
        return isinstance(granted, list) and any(role in granted for role in roles)

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def commit(self) -> None:
        await self.session.commit()


def cart_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Cart.buyer),
        selectinload(Cart.items),
        selectinload(Cart.seller),
    )


def order_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Order.buyer),
        selectinload(Order.cart),
        selectinload(Order.disputes).selectinload(Dispute.opened_by),
        # Not .selectinload(Dispute.order): that is this order, and with populate_existing it
        # would be reloaded without these options, leaving cart unloaded (a 500 on async).
        selectinload(Order.disputes).selectinload(Dispute.resolved_by),
        selectinload(Order.items),
        selectinload(Order.payments).selectinload(Payment.refunds),
        selectinload(Order.payouts).selectinload(Payout.seller),
        selectinload(Order.refunds),
        selectinload(Order.seller),
        selectinload(Order.shipments),
    )


def dispute_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Dispute.opened_by),
        selectinload(Dispute.order),
        selectinload(Dispute.resolved_by),
    )
