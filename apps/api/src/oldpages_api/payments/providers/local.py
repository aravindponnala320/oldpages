from __future__ import annotations

import uuid
from typing import Any

from oldpages_api.payments.providers.base import PaymentProvider, ShippingProvider


class LocalPaymentProvider(PaymentProvider):
    """Local/test payment provider that always succeeds. Used in development."""

    async def initiate_payment(
        self,
        order_id: str,
        amount_cents: int,
        currency: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        provider_payment_id = f"local_pay_{uuid.uuid4().hex}"
        return {
            "provider": "local",
            "provider_payment_id": provider_payment_id,
            "status": "authorized",
            "amount_cents": amount_cents,
            "currency": currency,
            "order_id": order_id,
            "redirect_url": None,
        }

    async def capture_payment(
        self,
        provider_payment_id: str,
        amount_cents: int,
    ) -> dict[str, Any]:
        return {
            "provider_payment_id": provider_payment_id,
            "status": "captured",
            "amount_cents": amount_cents,
        }

    async def refund_payment(
        self,
        provider_payment_id: str,
        amount_cents: int,
        reason: str,
    ) -> dict[str, Any]:
        provider_refund_id = f"local_refund_{uuid.uuid4().hex}"
        return {
            "provider_refund_id": provider_refund_id,
            "provider_payment_id": provider_payment_id,
            "status": "succeeded",
            "amount_cents": amount_cents,
            "reason": reason,
        }

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        # Local provider always accepts webhooks in development.
        return True


class LocalShippingProvider(ShippingProvider):
    """Local/test shipping provider that always succeeds. Used in development."""

    async def create_shipment(
        self,
        order_id: str,
        from_addr: dict[str, Any],
        to_addr: dict[str, Any],
        weight_grams: int,
    ) -> dict[str, Any]:
        provider_shipment_id = f"local_ship_{uuid.uuid4().hex}"
        tracking_number = f"LOCAL{uuid.uuid4().hex[:10].upper()}"
        return {
            "provider": "local",
            "provider_shipment_id": provider_shipment_id,
            "tracking_number": tracking_number,
            "carrier": "Local Courier",
            "status": "label_generated",
            "order_id": order_id,
            "label_url": None,
        }

    async def get_tracking(self, provider_shipment_id: str) -> dict[str, Any]:
        return {
            "provider_shipment_id": provider_shipment_id,
            "status": "in_transit",
            "events": [],
        }

    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        # Local provider always accepts webhooks in development.
        return True
