from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PaymentProvider(ABC):
    @abstractmethod
    async def initiate_payment(
        self,
        order_id: str,
        amount_cents: int,
        currency: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Initiate a payment and return provider-specific data."""
        ...

    @abstractmethod
    async def capture_payment(
        self,
        provider_payment_id: str,
        amount_cents: int,
    ) -> dict[str, Any]:
        """Capture an authorised payment."""
        ...

    @abstractmethod
    async def refund_payment(
        self,
        provider_payment_id: str,
        amount_cents: int,
        reason: str,
    ) -> dict[str, Any]:
        """Initiate a refund against a captured payment."""
        ...

    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify the authenticity of an incoming webhook payload."""
        ...


class ShippingProvider(ABC):
    @abstractmethod
    async def create_shipment(
        self,
        order_id: str,
        from_addr: dict[str, Any],
        to_addr: dict[str, Any],
        weight_grams: int,
    ) -> dict[str, Any]:
        """Create a shipment and return provider-specific tracking data."""
        ...

    @abstractmethod
    async def get_tracking(self, provider_shipment_id: str) -> dict[str, Any]:
        """Fetch current tracking info for a shipment."""
        ...

    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify the authenticity of an incoming shipping webhook payload."""
        ...
