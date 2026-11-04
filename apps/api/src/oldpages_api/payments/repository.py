from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

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
            .options(selectinload(Payment.order))
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
            .options(selectinload(Payment.order))
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

    # --- Session helpers ---

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

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
        selectinload(Order.disputes).selectinload(Dispute.order),
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
