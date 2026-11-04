from __future__ import annotations

from oldpages_api.core.errors import AppError


class SubscriptionPlanNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Subscription plan not found.",
            status_code=404,
            title="Subscription Plan Not Found",
            type_uri="https://oldpages.in/problems/subscription-plan-not-found",
        )


class SubscriptionNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Subscription not found.",
            status_code=404,
            title="Subscription Not Found",
            type_uri="https://oldpages.in/problems/subscription-not-found",
        )


class PromotionNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Promotion not found.",
            status_code=404,
            title="Promotion Not Found",
            type_uri="https://oldpages.in/problems/promotion-not-found",
        )


class CouponNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Coupon not found.",
            status_code=404,
            title="Coupon Not Found",
            type_uri="https://oldpages.in/problems/coupon-not-found",
        )


class CouponExpiredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="This coupon has expired.",
            status_code=410,
            title="Coupon Expired",
            type_uri="https://oldpages.in/problems/coupon-expired",
        )


class CouponExhaustedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="This coupon has reached its usage limit.",
            status_code=410,
            title="Coupon Exhausted",
            type_uri="https://oldpages.in/problems/coupon-exhausted",
        )


class SubscriptionValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Subscription Request",
            type_uri="https://oldpages.in/problems/invalid-subscription-request",
        )


class ForbiddenSubscriptionActionError(AppError):
    def __init__(self, detail: str = "This subscription action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )
