from __future__ import annotations

import logging
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.commerce.models import Offer
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.listings.models import Listing
from oldpages_api.payments.events import (
    DISPUTE_OPENED,
    DISPUTE_RESOLVED,
    ORDER_ACCEPTED,
    ORDER_CANCELLED,
    ORDER_CREATED,
    PAYOUT_INITIATED,
    REFUND_INITIATED,
    SHIPMENT_CREATED,
)
from oldpages_api.payments.exceptions import (
    CartNotFoundError,
    DisputeNotFoundError,
    ForbiddenPaymentsActionError,
    InvalidOrderStateTransitionError,
    OrderNotFoundError,
    PaymentProviderError,
    PaymentsValidationError,
    ShipmentNotFoundError,
)
from oldpages_api.payments.models import (
    Cart,
    CartItem,
    Dispute,
    Order,
    OrderItem,
    Payment,
    Payout,
    Refund,
    Shipment,
    WebhookEvent,
)
from oldpages_api.payments.permissions import (
    require_cart_owner,
    require_dispute_participant,
    require_order_buyer,
    require_order_participant,
    require_order_seller,
)
from oldpages_api.payments.providers.base import PaymentProvider, ShippingProvider
from oldpages_api.payments.providers.local import LocalPaymentProvider, LocalShippingProvider
from oldpages_api.payments.repository import PaymentsRepository
from oldpages_api.payments.schemas import (
    CartCheckoutRequest,
    CartCreateRequest,
    CartItemAddRequest,
    CartItemResponse,
    CartResponse,
    CartStatus,
    DisputeEvidenceRequest,
    DisputeOpenRequest,
    DisputeReason,
    DisputeResolveRequest,
    DisputeResponse,
    DisputeStatus,
    FulfillmentMethod,
    OrderCancelRequest,
    OrderItemResponse,
    OrderResponse,
    OrderStatus,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentResponse,
    PaymentStatus,
    PaymentsUserSummary,
    PayoutResponse,
    PayoutStatus,
    RefundInitiateRequest,
    RefundResponse,
    RefundStatus,
    ShipmentCreateRequest,
    ShipmentResponse,
    ShipmentStatus,
    ShipmentStatusUpdateRequest,
)
from oldpages_api.payments.schemas import (
    PaymentProvider as PaymentProviderLiteral,
)
from oldpages_api.payments.schemas import (
    ShipmentProvider as ShipmentProviderLiteral,
)

logger = logging.getLogger(__name__)

PAYMENT_PROVIDERS: dict[str, PaymentProvider] = {
    "local": LocalPaymentProvider(),
}

SHIPPING_PROVIDERS: dict[str, ShippingProvider] = {
    "local": LocalShippingProvider(),
}


class PaymentsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = PaymentsRepository(session)

    # --- Cart ---

    async def create_cart(
        self,
        payload: CartCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> CartResponse:
        seller = await self._resolve_user_by_public_id(payload.seller_id)
        if seller is None:
            raise PaymentsValidationError("Seller not found.")
        if seller.id == actor.id:
            raise PaymentsValidationError("Buyers cannot create a cart with themselves as seller.")
        existing = await self.repo.get_active_cart_for_buyer_seller(actor.id, seller.id)
        if existing is not None:
            return cart_response(existing)
        cart = Cart(
            buyer_user_id=actor.id,
            seller_user_id=seller.id,
            status="active",
        )
        self.repo.add(cart)
        await self.repo.flush()
        await self.audit(
            action=ORDER_CREATED,
            actor=actor,
            context=context,
            payload={"cart_id": cart.public_id},
            target_user_id=seller.id,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_cart_by_public_id(cart.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Cart could not be loaded.")
        return cart_response(reloaded)

    async def add_cart_item(
        self,
        cart_id: str,
        payload: CartItemAddRequest,
        actor: User,
    ) -> CartResponse:
        cart = await self._get_cart(cart_id)
        require_cart_owner(cart, actor)
        if cart.status != "active":
            raise InvalidOrderStateTransitionError("Only active carts can be modified.")
        listing = await self._resolve_listing_by_public_id(payload.listing_id)
        if listing is None:
            raise PaymentsValidationError("Listing not found.")
        if listing.seller_user_id != cart.seller_user_id:
            raise PaymentsValidationError("Listing does not belong to the cart's seller.")
        if listing.status != "active":
            raise PaymentsValidationError("Listing is not available.")
        price_cents = listing.price_amount_cents or 0
        item = CartItem(
            cart_id=cart.id,
            currency="INR",
            listing_id=listing.id,
            price_snapshot_cents=price_cents,
            quantity=payload.quantity,
        )
        self.repo.add(item)
        await self.repo.commit()
        reloaded = await self.repo.get_cart_by_public_id(cart.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Cart could not be loaded.")
        return cart_response(reloaded)

    async def remove_cart_item(
        self,
        cart_id: str,
        item_id: str,
        actor: User,
    ) -> CartResponse:
        cart = await self._get_cart(cart_id)
        require_cart_owner(cart, actor)
        if cart.status != "active":
            raise InvalidOrderStateTransitionError("Only active carts can be modified.")
        item = await self.repo.get_cart_item_by_public_id(item_id)
        if item is None or item.cart_id != cart.id:
            raise PaymentsValidationError("Cart item not found.")
        await self.repo.delete(item)
        await self.repo.commit()
        reloaded = await self.repo.get_cart_by_public_id(cart.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Cart could not be loaded.")
        return cart_response(reloaded)

    async def checkout_cart(
        self,
        cart_id: str,
        payload: CartCheckoutRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OrderResponse:
        cart = await self._get_cart(cart_id)
        require_cart_owner(cart, actor)
        if cart.status != "active":
            raise InvalidOrderStateTransitionError("Only active carts can be checked out.")
        if not cart.items:
            raise PaymentsValidationError("Cart has no items.")
        subtotal = sum(item.price_snapshot_cents * item.quantity for item in cart.items)
        platform_fee = int(subtotal * 0.025)
        total = subtotal + platform_fee
        order = Order(
            buyer_user_id=actor.id,
            cart_id=cart.id,
            currency="INR",
            fulfillment_method=payload.fulfillment_method,
            idempotency_key=payload.idempotency_key,
            metadata_json={},
            platform_fee_cents=platform_fee,
            seller_user_id=cart.seller_user_id,
            status="awaiting_payment",
            subtotal_cents=subtotal,
            total_cents=total,
        )
        self.repo.add(order)
        await self.repo.flush()
        for cart_item in cart.items:
            self.repo.add(
                OrderItem(
                    condition_snapshot="",
                    currency=cart_item.currency,
                    listing_id=cart_item.listing_id,
                    order_id=order.id,
                    quantity=cart_item.quantity,
                    title_snapshot="",
                    unit_price_cents=cart_item.price_snapshot_cents,
                )
            )
        cart.status = "checked_out"
        await self.audit(
            action=ORDER_CREATED,
            actor=actor,
            context=context,
            payload={"order_id": order.public_id, "cart_id": cart.public_id},
            target_user_id=cart.seller_user_id,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_order_by_public_id(order.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Order could not be loaded.")
        return order_response(reloaded)

    async def create_order_from_offer(
        self,
        offer_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OrderResponse:
        offer = await self._resolve_offer_by_public_id(offer_id)
        if offer is None:
            raise PaymentsValidationError("Offer not found.")
        if offer.buyer_user_id != actor.id and offer.seller_user_id != actor.id:
            raise ForbiddenPaymentsActionError("Only offer participants can create an order.")
        if offer.status != "accepted":
            raise InvalidOrderStateTransitionError("Only accepted offers can generate an order.")
        amount = offer.amount_cents or 0
        platform_fee = int(amount * 0.025)
        total = amount + platform_fee
        order = Order(
            buyer_user_id=offer.buyer_user_id,
            currency=offer.currency,
            fulfillment_method=cast("FulfillmentMethod", offer.fulfillment_method),
            metadata_json={},
            offer_id=offer.id,
            platform_fee_cents=platform_fee,
            seller_user_id=offer.seller_user_id,
            status="awaiting_payment",
            subtotal_cents=amount,
            total_cents=total,
        )
        self.repo.add(order)
        await self.repo.flush()
        self.repo.add(
            OrderItem(
                condition_snapshot="",
                currency=offer.currency,
                listing_id=offer.listing_id,
                order_id=order.id,
                quantity=offer.quantity,
                title_snapshot="",
                unit_price_cents=amount,
            )
        )
        await self.audit(
            action=ORDER_CREATED,
            actor=actor,
            context=context,
            payload={"order_id": order.public_id, "offer_id": offer.public_id},
            target_user_id=(
                offer.seller_user_id if actor.id == offer.buyer_user_id else offer.buyer_user_id
            ),
        )
        await self.repo.commit()
        reloaded = await self.repo.get_order_by_public_id(order.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Order could not be loaded.")
        return order_response(reloaded)

    async def accept_order(
        self,
        order_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OrderResponse:
        order = await self._get_order(order_id)
        require_order_seller(order, actor)
        if order.status not in {"paid"}:
            raise InvalidOrderStateTransitionError(
                "Only paid orders can be accepted by the seller."
            )
        order.status = "accepted"
        await self.audit(
            action=ORDER_ACCEPTED,
            actor=actor,
            context=context,
            payload={"order_id": order.public_id},
            target_user_id=order.buyer_user_id,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_order_by_public_id(order.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Order could not be loaded.")
        return order_response(reloaded)

    async def cancel_order(
        self,
        order_id: str,
        payload: OrderCancelRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> OrderResponse:
        order = await self._get_order(order_id)
        require_order_participant(order, actor)
        cancellable = {"created", "awaiting_payment", "paid", "accepted", "preparing"}
        if order.status not in cancellable:
            raise InvalidOrderStateTransitionError(
                f"Orders with status '{order.status}' cannot be cancelled."
            )
        order.status = "cancelled"
        order.metadata_json = {**order.metadata_json, "cancel_reason": payload.reason}
        await self.audit(
            action=ORDER_CANCELLED,
            actor=actor,
            context=context,
            payload={"order_id": order.public_id, "reason": payload.reason},
            target_user_id=(
                order.seller_user_id if actor.id == order.buyer_user_id else order.buyer_user_id
            ),
        )
        await self.repo.commit()
        reloaded = await self.repo.get_order_by_public_id(order.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Order could not be loaded.")
        return order_response(reloaded)

    # --- Payment ---

    async def initiate_payment(
        self,
        order_id: str,
        payload: PaymentInitiateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> PaymentInitiateResponse:
        order = await self._get_order(order_id)
        require_order_buyer(order, actor)
        if order.status != "awaiting_payment":
            raise InvalidOrderStateTransitionError(
                "Payments can only be initiated for orders awaiting payment."
            )
        existing = await self.repo.get_payment_by_idempotency_key(payload.idempotency_key, order.id)
        if existing is not None:
            provider_data: dict[str, Any] = existing.provider_metadata_json
            return PaymentInitiateResponse(
                payment=payment_response(existing, order),
                provider_data=provider_data,
            )
        provider = PAYMENT_PROVIDERS.get(payload.provider)
        if provider is None:
            raise PaymentsValidationError(f"Unknown payment provider: {payload.provider}")
        try:
            provider_data = await provider.initiate_payment(
                order_id=order.public_id,
                amount_cents=order.total_cents,
                currency=order.currency,
                metadata=payload.metadata,
            )
        except Exception as exc:
            logger.error("Payment provider error for order %s: %s", order.public_id, exc)
            raise PaymentProviderError("Payment initiation failed.") from exc
        payment = Payment(
            amount_cents=order.total_cents,
            currency=order.currency,
            idempotency_key=payload.idempotency_key,
            order_id=order.id,
            provider=payload.provider,
            provider_metadata_json=provider_data,
            provider_payment_id=provider_data.get("provider_payment_id"),
            status="authorized",
        )
        self.repo.add(payment)
        await self.repo.commit()
        reloaded_payment = await self.repo.get_payment_by_public_id(payment.public_id)
        if reloaded_payment is None:
            raise PaymentsValidationError("Payment could not be loaded.")
        return PaymentInitiateResponse(
            payment=payment_response(reloaded_payment, order),
            provider_data=provider_data,
        )

    async def handle_payment_webhook(
        self,
        provider: str,
        payload: bytes,
        signature: str,
    ) -> dict[str, str]:
        payment_provider = PAYMENT_PROVIDERS.get(provider)
        if payment_provider is None:
            raise PaymentsValidationError(f"Unknown payment provider: {provider}")
        if not payment_provider.verify_webhook(payload, signature):
            raise PaymentsValidationError("Invalid webhook signature.")
        import json

        try:
            data = cast("dict[str, Any]", json.loads(payload))
        except Exception as exc:
            raise PaymentsValidationError("Invalid webhook payload.") from exc
        provider_event_id = data.get("event_id") or data.get("id") or ""
        if not isinstance(provider_event_id, str) or not provider_event_id.strip():
            raise PaymentsValidationError("Webhook event id is required.")
        provider_event_id = provider_event_id.strip()
        event_type = data.get("event") or data.get("type") or "unknown"
        existing_event = await self.repo.get_webhook_event_by_provider_event_id(
            provider, provider_event_id
        )
        if existing_event is not None and existing_event.processed:
            return {"status": "already_processed"}
        webhook_event = WebhookEvent(
            event_type=event_type,
            payload_json=data,
            processed=False,
            provider=provider,
            provider_event_id=provider_event_id,
        )
        self.repo.add(webhook_event)
        await self.repo.flush()
        payment = await self._payment_from_webhook(provider, data)
        if payment is not None:
            self._apply_payment_webhook(payment, event_type, data)
        webhook_event.processed = True
        webhook_event.processed_at = utc_now()
        await self.repo.commit()
        return {"status": "processed"}

    # --- Payout ---

    async def initiate_payout(
        self,
        order_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> PayoutResponse:
        order = await self._get_order(order_id)
        require_order_seller(order, actor)
        if order.status not in {"completed", "delivered"}:
            raise InvalidOrderStateTransitionError(
                "Payouts can only be initiated for completed or delivered orders."
            )
        payout_amount = payout_available_cents(order)
        if payout_amount <= 0:
            raise PaymentsValidationError("No captured funds are available for payout.")
        payout = Payout(
            amount_cents=payout_amount,
            currency=order.currency,
            initiated_at=utc_now(),
            order_id=order.id,
            provider="local",
            seller_user_id=order.seller_user_id,
            paid_at=utc_now(),
            status="paid",
        )
        self.repo.add(payout)
        await self.audit(
            action=PAYOUT_INITIATED,
            actor=actor,
            context=context,
            payload={"order_id": order.public_id},
            target_user_id=order.seller_user_id,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_payout_by_public_id(payout.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Payout could not be loaded.")
        return payout_response(reloaded)

    # --- Refund ---

    async def initiate_refund(
        self,
        order_id: str,
        payload: RefundInitiateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> RefundResponse:
        order = await self._get_order(order_id)
        require_order_participant(order, actor)
        if order.status not in {"paid", "accepted", "preparing", "cancelled"}:
            raise InvalidOrderStateTransitionError(
                "Refunds can only be initiated for paid or cancelled orders."
            )
        captured_payment = next((p for p in order.payments if p.status == "captured"), None)
        if captured_payment is None:
            raise PaymentsValidationError("No captured payment found for this order.")
        available_to_refund = refund_available_cents(captured_payment)
        refund_amount = payload.amount_cents or available_to_refund
        if refund_amount > available_to_refund:
            raise PaymentsValidationError("Refund amount exceeds captured payment amount.")
        provider = PAYMENT_PROVIDERS.get(captured_payment.provider)
        if provider is None:
            raise PaymentsValidationError(f"Unknown payment provider: {captured_payment.provider}")
        if captured_payment.provider_payment_id is None:
            raise PaymentsValidationError("Captured payment is missing provider payment id.")
        try:
            provider_data = await provider.refund_payment(
                captured_payment.provider_payment_id,
                refund_amount,
                payload.reason,
            )
        except Exception as exc:
            logger.error("Payment refund provider error for order %s: %s", order.public_id, exc)
            raise PaymentProviderError("Refund initiation failed.") from exc
        refund = Refund(
            amount_cents=refund_amount,
            currency=order.currency,
            initiated_at=utc_now(),
            order_id=order.id,
            payment_id=captured_payment.id,
            provider_refund_id=provider_data.get("provider_refund_id"),
            reason=payload.reason,
            status=cast("RefundStatus", provider_data.get("status", "processing")),
            succeeded_at=utc_now() if provider_data.get("status") == "succeeded" else None,
        )
        self.repo.add(refund)
        if refund.status == "succeeded" and refund_amount >= available_to_refund:
            captured_payment.status = "refunded"
            captured_payment.refunded_at = utc_now()
            order.status = "refunded"
        await self.audit(
            action=REFUND_INITIATED,
            actor=actor,
            context=context,
            payload={"order_id": order.public_id, "reason": payload.reason},
            target_user_id=(
                order.seller_user_id if actor.id == order.buyer_user_id else order.buyer_user_id
            ),
        )
        await self.repo.commit()
        reloaded = await self.repo.get_refund_by_public_id(refund.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Refund could not be loaded.")
        return refund_response(reloaded)

    # --- Shipment ---

    async def create_shipment(
        self,
        payload: ShipmentCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ShipmentResponse:
        order = await self._get_order(payload.order_id)
        require_order_seller(order, actor)
        if order.fulfillment_method != "shipping":
            raise PaymentsValidationError("Only shipping orders can have shipments.")
        if order.status not in {"accepted", "preparing"}:
            raise InvalidOrderStateTransitionError(
                "Shipments can only be created for accepted or preparing orders."
            )
        shipping_provider = SHIPPING_PROVIDERS.get(payload.provider)
        if shipping_provider is None:
            raise PaymentsValidationError(f"Unknown shipping provider: {payload.provider}")
        from_addr = payload.from_address.model_dump()
        to_addr = payload.to_address.model_dump()
        try:
            provider_data = await shipping_provider.create_shipment(
                order_id=order.public_id,
                from_addr=from_addr,
                to_addr=to_addr,
                weight_grams=payload.weight_grams or 500,
            )
        except Exception as exc:
            logger.error("Shipping provider error for order %s: %s", order.public_id, exc)
            raise PaymentsValidationError("Shipment creation failed.") from exc
        shipment = Shipment(
            carrier=provider_data.get("carrier"),
            from_address_json=from_addr,
            order_id=order.id,
            provider=payload.provider,
            provider_metadata_json=provider_data,
            provider_shipment_id=provider_data.get("provider_shipment_id"),
            status=cast("ShipmentStatus", provider_data.get("status", "pending")),
            to_address_json=to_addr,
            tracking_number=provider_data.get("tracking_number"),
            weight_grams=payload.weight_grams,
        )
        self.repo.add(shipment)
        order.status = "preparing"
        await self.audit(
            action=SHIPMENT_CREATED,
            actor=actor,
            context=context,
            payload={"order_id": order.public_id},
            target_user_id=order.buyer_user_id,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_shipment_by_public_id(shipment.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Shipment could not be loaded.")
        return shipment_response(reloaded)

    async def update_shipping_status(
        self,
        shipment_id: str,
        payload: ShipmentStatusUpdateRequest,
        actor: User,
    ) -> ShipmentResponse:
        shipment = await self._get_shipment(shipment_id)
        require_order_seller(shipment.order, actor)
        shipment.status = payload.status
        if payload.tracking_number is not None:
            shipment.tracking_number = payload.tracking_number
        if payload.carrier is not None:
            shipment.carrier = payload.carrier
        if payload.estimated_delivery_at is not None:
            shipment.estimated_delivery_at = payload.estimated_delivery_at
        if payload.status == "delivered":
            shipment.delivered_at = utc_now()
            shipment.order.status = "delivered"
        await self.repo.commit()
        reloaded = await self.repo.get_shipment_by_public_id(shipment.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Shipment could not be loaded.")
        return shipment_response(reloaded)

    async def handle_shipping_webhook(
        self,
        provider: str,
        payload: bytes,
        signature: str,
    ) -> dict[str, str]:
        shipping_provider = SHIPPING_PROVIDERS.get(provider)
        if shipping_provider is None:
            raise PaymentsValidationError(f"Unknown shipping provider: {provider}")
        if not shipping_provider.verify_webhook(payload, signature):
            raise PaymentsValidationError("Invalid shipping webhook signature.")
        import json

        try:
            data = cast("dict[str, Any]", json.loads(payload))
        except Exception as exc:
            raise PaymentsValidationError("Invalid shipping webhook payload.") from exc
        provider_event_id = data.get("event_id") or data.get("id") or ""
        if not isinstance(provider_event_id, str) or not provider_event_id.strip():
            raise PaymentsValidationError("Shipping webhook event id is required.")
        provider_event_id = provider_event_id.strip()
        event_type = data.get("event") or data.get("type") or "unknown"
        existing_event = await self.repo.get_webhook_event_by_provider_event_id(
            provider, provider_event_id
        )
        if existing_event is not None and existing_event.processed:
            return {"status": "already_processed"}
        webhook_event = WebhookEvent(
            event_type=event_type,
            payload_json=data,
            processed=False,
            provider=provider,
            provider_event_id=provider_event_id,
        )
        self.repo.add(webhook_event)
        await self.repo.flush()
        shipment = await self._shipment_from_webhook(data)
        if shipment is not None:
            self._apply_shipping_webhook(shipment, data)
        webhook_event.processed = True
        webhook_event.processed_at = utc_now()
        await self.repo.commit()
        return {"status": "processed"}

    # --- Dispute ---

    async def open_dispute(
        self,
        payload: DisputeOpenRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> DisputeResponse:
        order = await self._get_order(payload.order_id)
        require_order_buyer(order, actor)
        disputable = {"paid", "accepted", "preparing", "shipped", "delivered"}
        if order.status not in disputable:
            raise InvalidOrderStateTransitionError("Disputes can only be opened for active orders.")
        dispute = Dispute(
            description=payload.description,
            evidence_json={},
            opened_by_user_id=actor.id,
            order_id=order.id,
            reason=payload.reason,
            status="opened",
        )
        self.repo.add(dispute)
        order.status = "disputed"
        await self.audit(
            action=DISPUTE_OPENED,
            actor=actor,
            context=context,
            payload={"order_id": order.public_id, "reason": payload.reason},
            target_user_id=order.seller_user_id,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_dispute_by_public_id(dispute.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Dispute could not be loaded.")
        return dispute_response(reloaded)

    async def add_dispute_evidence(
        self,
        dispute_id: str,
        payload: DisputeEvidenceRequest,
        actor: User,
    ) -> DisputeResponse:
        dispute = await self._get_dispute(dispute_id)
        require_dispute_participant(dispute, actor)
        if dispute.status not in {"opened", "under_review"}:
            raise InvalidOrderStateTransitionError(
                "Evidence can only be added to open or under-review disputes."
            )
        merged = {**dispute.evidence_json, **payload.evidence}
        if payload.note:
            notes = merged.get("notes", [])
            if isinstance(notes, list):
                notes.append({"user_id": actor.public_id, "note": payload.note})
            merged["notes"] = notes
        dispute.evidence_json = merged
        dispute.status = "under_review"
        await self.repo.commit()
        reloaded = await self.repo.get_dispute_by_public_id(dispute.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Dispute could not be loaded.")
        return dispute_response(reloaded)

    async def resolve_dispute(
        self,
        dispute_id: str,
        payload: DisputeResolveRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> DisputeResponse:
        dispute = await self._get_dispute(dispute_id)
        if dispute.status not in {"opened", "under_review"}:
            raise InvalidOrderStateTransitionError("Only open disputes can be resolved.")
        dispute.status = cast("DisputeStatus", payload.resolution)
        dispute.resolved_by_user_id = actor.id
        dispute.resolution_note = payload.resolution_note
        dispute.resolved_at = utc_now()
        if payload.resolution in {"resolved_buyer", "resolved_seller", "closed"}:
            dispute.order.status = "completed"
        await self.audit(
            action=DISPUTE_RESOLVED,
            actor=actor,
            context=context,
            payload={"dispute_id": dispute.public_id, "resolution": payload.resolution},
            target_user_id=dispute.opened_by_user_id,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_dispute_by_public_id(dispute.public_id)
        if reloaded is None:
            raise PaymentsValidationError("Dispute could not be loaded.")
        return dispute_response(reloaded)

    # --- Internal helpers ---

    async def _get_cart(self, cart_id: str) -> Cart:
        cart = await self.repo.get_cart_by_public_id(cart_id)
        if cart is None:
            raise CartNotFoundError()
        return cart

    async def _get_order(self, order_id: str) -> Order:
        order = await self.repo.get_order_by_public_id(order_id)
        if order is None:
            raise OrderNotFoundError()
        return order

    async def _get_shipment(self, shipment_id: str) -> Shipment:
        shipment = await self.repo.get_shipment_by_public_id(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError()
        return shipment

    async def _get_dispute(self, dispute_id: str) -> Dispute:
        dispute = await self.repo.get_dispute_by_public_id(dispute_id)
        if dispute is None:
            raise DisputeNotFoundError()
        return dispute

    async def _resolve_user_by_public_id(self, public_id: str) -> User | None:
        from sqlalchemy import select as sa_select

        from oldpages_api.identity.models import User as UserModel

        result = await self.repo.session.execute(
            sa_select(UserModel).where(UserModel.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def _resolve_listing_by_public_id(self, public_id: str) -> Listing | None:
        from sqlalchemy import select as sa_select

        result = await self.repo.session.execute(
            sa_select(Listing).where(Listing.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def _resolve_offer_by_public_id(self, public_id: str) -> Offer | None:
        from sqlalchemy import select as sa_select

        result = await self.repo.session.execute(
            sa_select(Offer).where(Offer.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def _payment_from_webhook(
        self,
        provider: str,
        data: dict[str, Any],
    ) -> Payment | None:
        public_id = data.get("payment_public_id") or data.get("payment_id")
        if isinstance(public_id, str):
            payment = await self.repo.get_payment_by_public_id(public_id)
            if payment is not None:
                return payment
        provider_payment_id = data.get("provider_payment_id")
        if isinstance(provider_payment_id, str):
            payment = await self.repo.get_payment_by_provider_payment_id(
                provider,
                provider_payment_id,
            )
            if payment is not None:
                return payment
        order_public_id = data.get("order_id")
        if isinstance(order_public_id, str):
            order = await self.repo.get_order_by_public_id(order_public_id)
            if order is not None:
                return next(
                    (payment for payment in order.payments if payment.provider == provider),
                    None,
                )
        return None

    def _apply_payment_webhook(
        self,
        payment: Payment,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        normalized = f"{event_type} {data.get('status', '')}".lower()
        is_refund_event = "refund" in normalized
        if "refunded" in normalized or (is_refund_event and "succeeded" in normalized):
            payment.status = "refunded"
            payment.refunded_at = payment.refunded_at or utc_now()
            payment.order.status = "refunded"
            return
        if any(token in normalized for token in ("captured", "succeeded", "paid")):
            payment.status = "captured"
            payment.captured_at = payment.captured_at or utc_now()
            payment.order.status = "paid"
            return
        if "authorized" in normalized:
            payment.status = "authorized"
            return
        if "failed" in normalized:
            payment.status = "failed"
            payment.failed_at = payment.failed_at or utc_now()
            return

    async def _shipment_from_webhook(self, data: dict[str, Any]) -> Shipment | None:
        shipment_public_id = data.get("shipment_id")
        if isinstance(shipment_public_id, str):
            shipment = await self.repo.get_shipment_by_public_id(shipment_public_id)
            if shipment is not None:
                return shipment
        provider_shipment_id = data.get("provider_shipment_id")
        if isinstance(provider_shipment_id, str):
            return await self.repo.get_shipment_by_provider_id(provider_shipment_id)
        return None

    def _apply_shipping_webhook(self, shipment: Shipment, data: dict[str, Any]) -> None:
        status = data.get("status")
        if isinstance(status, str) and status:
            shipment.status = cast("ShipmentStatus", status)
            if status == "delivered":
                shipment.delivered_at = shipment.delivered_at or utc_now()
                shipment.order.status = "delivered"
            elif status in {"picked_up", "in_transit"}:
                shipment.order.status = "shipped"
        tracking_number = data.get("tracking_number")
        if isinstance(tracking_number, str) and tracking_number:
            shipment.tracking_number = tracking_number
        carrier = data.get("carrier")
        if isinstance(carrier, str) and carrier:
            shipment.carrier = carrier

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


# --- Response builders ---


def cart_response(cart: Cart) -> CartResponse:
    return CartResponse(
        buyer=PaymentsUserSummary(id=cart.buyer.public_id),
        created_at=cart.created_at,
        currency="INR",
        id=cart.public_id,
        items=[
            CartItemResponse(
                cart_id=cart.public_id,
                created_at=item.created_at,
                currency=item.currency,
                id=item.public_id,
                listing_id=str(item.listing_id),
                price_snapshot_cents=item.price_snapshot_cents,
                quantity=item.quantity,
            )
            for item in cart.items
        ],
        seller=PaymentsUserSummary(id=cart.seller.public_id),
        status=cast("CartStatus", cart.status),
    )


def order_response(order: Order) -> OrderResponse:
    offer_public_id: str | None = None
    if order.offer_id is not None:
        # offer_id is int; we expose it as None since we don't eagerly load offer here
        offer_public_id = None

    cart_public_id: str | None = None
    if order.cart is not None:
        cart_public_id = order.cart.public_id

    return OrderResponse(
        buyer=PaymentsUserSummary(id=order.buyer.public_id),
        cart_id=cart_public_id,
        created_at=order.created_at,
        currency=order.currency,
        fulfillment_method=cast("FulfillmentMethod", order.fulfillment_method),
        id=order.public_id,
        idempotency_key=order.idempotency_key,
        items=[
            OrderItemResponse(
                condition_snapshot=item.condition_snapshot,
                currency=item.currency,
                id=item.public_id,
                listing_id=str(item.listing_id),
                order_id=order.public_id,
                quantity=item.quantity,
                title_snapshot=item.title_snapshot,
                unit_price_cents=item.unit_price_cents,
            )
            for item in order.items
        ],
        offer_id=offer_public_id,
        platform_fee_cents=order.platform_fee_cents,
        seller=PaymentsUserSummary(id=order.seller.public_id),
        status=cast("OrderStatus", order.status),
        subtotal_cents=order.subtotal_cents,
        total_cents=order.total_cents,
    )


def payment_response(payment: Payment, order: Order) -> PaymentResponse:
    return PaymentResponse(
        amount_cents=payment.amount_cents,
        captured_at=payment.captured_at,
        created_at=payment.created_at,
        currency=payment.currency,
        failed_at=payment.failed_at,
        id=payment.public_id,
        idempotency_key=payment.idempotency_key,
        order_id=order.public_id,
        provider=cast("PaymentProviderLiteral", payment.provider),
        provider_payment_id=payment.provider_payment_id,
        refunded_at=payment.refunded_at,
        status=cast("PaymentStatus", payment.status),
    )


def captured_funds_cents(order: Order) -> int:
    return sum(payment.amount_cents for payment in order.payments if payment.status == "captured")


def refund_committed_cents(order: Order) -> int:
    return sum(
        refund.amount_cents
        for refund in order.refunds
        if refund.status in {"processing", "succeeded"}
    )


def payout_committed_cents(order: Order) -> int:
    return sum(
        payout.amount_cents for payout in order.payouts if payout.status in {"processing", "paid"}
    )


def payout_available_cents(order: Order) -> int:
    available = (
        captured_funds_cents(order)
        - order.platform_fee_cents
        - refund_committed_cents(order)
        - payout_committed_cents(order)
    )
    return max(available, 0)


def refund_available_cents(payment: Payment) -> int:
    refunded = sum(
        refund.amount_cents
        for refund in payment.refunds
        if refund.status in {"processing", "succeeded"}
    )
    return max(payment.amount_cents - refunded, 0)


def payout_response(payout: Payout) -> PayoutResponse:
    return PayoutResponse(
        amount_cents=payout.amount_cents,
        created_at=payout.created_at,
        currency=payout.currency,
        id=payout.public_id,
        initiated_at=payout.initiated_at,
        order_id=payout.order.public_id,
        paid_at=payout.paid_at,
        provider=payout.provider,
        provider_payout_id=payout.provider_payout_id,
        seller=PaymentsUserSummary(id=payout.seller.public_id),
        status=cast("PayoutStatus", payout.status),
    )


def refund_response(refund: Refund) -> RefundResponse:
    return RefundResponse(
        amount_cents=refund.amount_cents,
        created_at=refund.created_at,
        currency=refund.currency,
        id=refund.public_id,
        initiated_at=refund.initiated_at,
        order_id=refund.order.public_id,
        payment_id=refund.payment.public_id,
        provider_refund_id=refund.provider_refund_id,
        reason=refund.reason,
        status=cast("RefundStatus", refund.status),
        succeeded_at=refund.succeeded_at,
    )


def shipment_response(shipment: Shipment) -> ShipmentResponse:
    return ShipmentResponse(
        carrier=shipment.carrier,
        created_at=shipment.created_at,
        delivered_at=shipment.delivered_at,
        estimated_delivery_at=shipment.estimated_delivery_at,
        from_address=shipment.from_address_json,
        id=shipment.public_id,
        order_id=shipment.order.public_id,
        provider=cast("ShipmentProviderLiteral", shipment.provider),
        provider_shipment_id=shipment.provider_shipment_id,
        status=cast("ShipmentStatus", shipment.status),
        to_address=shipment.to_address_json,
        tracking_number=shipment.tracking_number,
        weight_grams=shipment.weight_grams,
    )


def dispute_response(dispute: Dispute) -> DisputeResponse:
    return DisputeResponse(
        created_at=dispute.created_at,
        description=dispute.description,
        evidence=dispute.evidence_json,
        id=dispute.public_id,
        opened_by=PaymentsUserSummary(id=dispute.opened_by.public_id),
        order_id=dispute.order.public_id,
        reason=cast("DisputeReason", dispute.reason),
        resolution_note=dispute.resolution_note,
        resolved_at=dispute.resolved_at,
        resolved_by=(
            PaymentsUserSummary(id=dispute.resolved_by.public_id) if dispute.resolved_by else None
        ),
        status=cast("DisputeStatus", dispute.status),
    )
