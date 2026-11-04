from __future__ import annotations

from oldpages_api.core.errors import AppError


class OfferNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Offer not found.",
            status_code=404,
            title="Offer Not Found",
            type_uri="https://oldpages.in/problems/offer-not-found",
        )


class PickupNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Pickup session not found.",
            status_code=404,
            title="Pickup Session Not Found",
            type_uri="https://oldpages.in/problems/pickup-not-found",
        )


class TransactionNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Transaction not found.",
            status_code=404,
            title="Transaction Not Found",
            type_uri="https://oldpages.in/problems/transaction-not-found",
        )


class ForbiddenCommerceActionError(AppError):
    def __init__(self, detail: str = "This commerce action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


class InvalidCommerceStateTransitionError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Invalid Commerce State Transition",
            type_uri="https://oldpages.in/problems/invalid-commerce-state-transition",
        )


class CommerceValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Commerce Request",
            type_uri="https://oldpages.in/problems/invalid-commerce-request",
        )
