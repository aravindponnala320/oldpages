from __future__ import annotations

from oldpages_api.core.errors import AppError


class OrderNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Order not found.",
            status_code=404,
            title="Order Not Found",
            type_uri="https://oldpages.in/problems/order-not-found",
        )


class PaymentNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Payment not found.",
            status_code=404,
            title="Payment Not Found",
            type_uri="https://oldpages.in/problems/payment-not-found",
        )


class ShipmentNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Shipment not found.",
            status_code=404,
            title="Shipment Not Found",
            type_uri="https://oldpages.in/problems/shipment-not-found",
        )


class DisputeNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Dispute not found.",
            status_code=404,
            title="Dispute Not Found",
            type_uri="https://oldpages.in/problems/dispute-not-found",
        )


class CartNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Cart not found.",
            status_code=404,
            title="Cart Not Found",
            type_uri="https://oldpages.in/problems/cart-not-found",
        )


class PaymentsValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Payments Request",
            type_uri="https://oldpages.in/problems/invalid-payments-request",
        )


class InvalidOrderStateTransitionError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Invalid Order State Transition",
            type_uri="https://oldpages.in/problems/invalid-order-state-transition",
        )


class IdempotencyConflictError(AppError):
    def __init__(
        self,
        detail: str = "A conflicting request with this idempotency key is in flight.",
    ) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Idempotency Conflict",
            type_uri="https://oldpages.in/problems/idempotency-conflict",
        )


class PaymentProviderError(AppError):
    def __init__(self, detail: str = "The payment provider returned an error.") -> None:
        super().__init__(
            detail=detail,
            status_code=502,
            title="Payment Provider Error",
            type_uri="https://oldpages.in/problems/payment-provider-error",
        )


class ForbiddenPaymentsActionError(AppError):
    def __init__(self, detail: str = "This payments action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )
