from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.models import User
from oldpages_api.identity.security import utc_now
from oldpages_api.subscriptions.exceptions import (
    ForbiddenSubscriptionActionError,
    PromotionNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionPlanNotFoundError,
    SubscriptionValidationError,
)
from oldpages_api.subscriptions.models import (
    Coupon,
    Promotion,
    PromotionOrder,
    Subscription,
    SubscriptionPlan,
)
from oldpages_api.subscriptions.permissions import (
    require_promotion_owner,
    require_subscription_owner,
)
from oldpages_api.subscriptions.repository import SubscriptionRepository
from oldpages_api.subscriptions.schemas import (
    BillingInterval,
    CouponCreateRequest,
    CouponResponse,
    CouponValidateRequest,
    CouponValidateResponse,
    DiscountType,
    PromotionCreateRequest,
    PromotionResponse,
    PromotionStatus,
    PromotionType,
    SubscribeRequest,
    SubscriptionEntitlementsResponse,
    SubscriptionPlanResponse,
    SubscriptionProvider,
    SubscriptionResponse,
    SubscriptionStatus,
)

FREE_ENTITLEMENT_LIMITS: dict[str, int | None] = {
    "community_limit": 3,
    "listing_limit": 10,
    "saved_search_limit": 5,
}


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SubscriptionRepository(session)

    async def list_plans(self) -> list[SubscriptionPlanResponse]:
        plans = await self.repo.list_plans()
        return [plan_response(p) for p in plans]

    async def subscribe(
        self,
        payload: SubscribeRequest,
        actor: User,
    ) -> SubscriptionResponse:
        plan = await self.repo.get_plan_by_public_id(payload.plan_id)
        if plan is None:
            raise SubscriptionPlanNotFoundError()
        existing = await self.current_subscription_for_user(actor.id)
        if existing is not None:
            raise SubscriptionValidationError("User already has an active subscription.")
        now = utc_now()
        period_days = 365 if plan.billing_interval == "yearly" else 30
        subscription = Subscription(
            user_id=actor.id,
            plan_id=plan.id,
            status="active",
            provider="local",
            current_period_start=now,
            current_period_end=now + timedelta(days=period_days),
        )
        self.repo.add(subscription)
        await self.repo.commit()
        reloaded = await self.repo.get_subscription_by_public_id(subscription.public_id)
        if reloaded is None:
            raise SubscriptionValidationError("Subscription could not be loaded.")
        return subscription_response(reloaded)

    async def cancel_subscription(
        self,
        subscription_id: str,
        actor: User,
    ) -> SubscriptionResponse:
        subscription = await self.repo.get_subscription_by_public_id(subscription_id)
        if subscription is None:
            raise SubscriptionNotFoundError()
        require_subscription_owner(subscription, actor)
        if subscription.status in {"cancelled", "expired"}:
            raise SubscriptionValidationError("Subscription is already cancelled or expired.")
        subscription.status = "cancelled"
        subscription.cancelled_at = utc_now()
        await self.repo.commit()
        reloaded = await self.repo.get_subscription_by_public_id(subscription.public_id)
        if reloaded is None:
            raise SubscriptionValidationError("Subscription could not be loaded.")
        return subscription_response(reloaded)

    async def get_my_subscription(self, actor: User) -> SubscriptionResponse:
        subscription = await self.current_subscription_for_user(actor.id)
        if subscription is None:
            raise SubscriptionNotFoundError()
        return subscription_response(subscription)

    async def get_my_entitlements(self, actor: User) -> SubscriptionEntitlementsResponse:
        subscription = await self.current_subscription_for_user(actor.id)
        return entitlements_response(subscription)

    async def create_promotion(
        self,
        payload: PromotionCreateRequest,
        actor: User,
    ) -> PromotionResponse:
        from sqlalchemy import select as sa_select

        from oldpages_api.listings.models import Listing

        result = await self.repo.session.execute(
            sa_select(Listing).where(Listing.public_id == payload.listing_id)
        )
        listing = result.scalar_one_or_none()
        if listing is None:
            raise SubscriptionValidationError("Listing not found.")
        if listing.seller_user_id != actor.id:
            raise ForbiddenSubscriptionActionError("You can only promote your own listings.")
        if payload.ends_at <= payload.starts_at:
            raise SubscriptionValidationError("Promotion end time must be after start time.")
        promotion = Promotion(
            listing_id=listing.id,
            seller_user_id=actor.id,
            type=payload.type,
            status="active",
            amount_cents=payload.amount_cents,
            currency=payload.currency,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
        )
        self.repo.add(promotion)
        await self.repo.flush()
        promotion_order = PromotionOrder(
            amount_cents=payload.amount_cents,
            currency=payload.currency,
            paid_at=utc_now(),
            promotion_id=promotion.id,
            provider="local",
            seller_user_id=actor.id,
            status="paid",
        )
        self.repo.add(promotion_order)
        await self.repo.commit()
        reloaded = await self.repo.get_promotion_by_public_id(promotion.public_id)
        if reloaded is None:
            raise SubscriptionValidationError("Promotion could not be loaded.")
        return promotion_response(reloaded)

    async def list_my_promotions(self, actor: User) -> list[PromotionResponse]:
        promotions = await self.repo.list_promotions_for_seller(actor.id)
        return [promotion_response(p) for p in promotions]

    async def cancel_promotion(
        self,
        promotion_id: str,
        actor: User,
    ) -> PromotionResponse:
        promotion = await self.repo.get_promotion_by_public_id(promotion_id)
        if promotion is None:
            raise PromotionNotFoundError()
        require_promotion_owner(promotion, actor)
        if promotion.status != "active":
            raise SubscriptionValidationError("Only active promotions can be cancelled.")
        promotion.status = "cancelled"
        await self.repo.commit()
        reloaded = await self.repo.get_promotion_by_public_id(promotion.public_id)
        if reloaded is None:
            raise SubscriptionValidationError("Promotion could not be loaded.")
        return promotion_response(reloaded)

    async def create_coupon(
        self,
        payload: CouponCreateRequest,
        actor: User,
    ) -> CouponResponse:
        if not getattr(actor, "is_superuser", False):
            raise ForbiddenSubscriptionActionError("Only admins can create coupons.")
        existing = await self.repo.get_coupon_by_code(payload.code)
        if existing is not None:
            raise SubscriptionValidationError("A coupon with this code already exists.")
        coupon = Coupon(
            code=payload.code,
            discount_type=payload.discount_type,
            discount_value=payload.discount_value,
            min_order_cents=payload.min_order_cents,
            max_uses=payload.max_uses,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            is_active=True,
        )
        self.repo.add(coupon)
        await self.repo.commit()
        reloaded = await self.repo.get_coupon_by_code(coupon.code)
        if reloaded is None:
            raise SubscriptionValidationError("Coupon could not be loaded.")
        return coupon_response(reloaded)

    async def validate_coupon(self, payload: CouponValidateRequest) -> CouponValidateResponse:
        coupon = await self.repo.get_coupon_by_code(payload.code)
        if coupon is None or not coupon.is_active:
            return CouponValidateResponse(
                valid=False, discount_cents=0, message="Coupon not found or inactive."
            )
        now = utc_now()
        valid_from = ensure_aware_datetime(coupon.valid_from)
        valid_until = (
            ensure_aware_datetime(coupon.valid_until) if coupon.valid_until is not None else None
        )
        if now < valid_from:
            return CouponValidateResponse(
                valid=False, discount_cents=0, message="Coupon is not yet valid."
            )
        if valid_until is not None and now > valid_until:
            return CouponValidateResponse(
                valid=False, discount_cents=0, message="Coupon has expired."
            )
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            return CouponValidateResponse(
                valid=False, discount_cents=0, message="Coupon usage limit reached."
            )
        if (
            coupon.min_order_cents is not None
            and payload.order_amount_cents < coupon.min_order_cents
        ):
            return CouponValidateResponse(
                valid=False,
                discount_cents=0,
                message=f"Minimum order amount is {coupon.min_order_cents} cents.",
            )
        if coupon.discount_type == "percent":
            discount_cents = int(payload.order_amount_cents * coupon.discount_value / 100)
        else:
            discount_cents = min(coupon.discount_value, payload.order_amount_cents)
        return CouponValidateResponse(
            valid=True,
            discount_cents=discount_cents,
            message="Coupon is valid.",
        )

    async def list_coupons(self, actor: User) -> list[CouponResponse]:
        if not getattr(actor, "is_superuser", False):
            raise ForbiddenSubscriptionActionError("Only admins can list coupons.")
        coupons = await self.repo.list_coupons()
        return [coupon_response(c) for c in coupons]

    async def current_subscription_for_user(self, user_id: int) -> Subscription | None:
        subscription = await self.repo.get_active_subscription_for_user(user_id)
        if subscription is None:
            return None
        if subscription.current_period_end is None:
            return subscription
        if ensure_aware_datetime(subscription.current_period_end) > utc_now():
            return subscription
        subscription.status = "expired"
        await self.repo.commit()
        return None


def ensure_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def plan_response(plan: SubscriptionPlan) -> SubscriptionPlanResponse:
    return SubscriptionPlanResponse(
        id=plan.public_id,
        name=plan.name,
        slug=plan.slug,
        description=plan.description,
        price_cents=plan.price_cents,
        billing_interval=cast("BillingInterval", plan.billing_interval),
        features_json=list(plan.features_json),
        listing_limit=plan.listing_limit,
        saved_search_limit=plan.saved_search_limit,
        community_limit=plan.community_limit,
        is_active=plan.is_active,
        sort_order=plan.sort_order,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def subscription_response(subscription: Subscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=subscription.public_id,
        user_id=subscription.user.public_id,
        plan=plan_response(subscription.plan),
        status=cast("SubscriptionStatus", subscription.status),
        provider=cast("SubscriptionProvider", subscription.provider),
        provider_subscription_id=subscription.provider_subscription_id,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancelled_at=subscription.cancelled_at,
        trial_end_at=subscription.trial_end_at,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


def entitlements_response(subscription: Subscription | None) -> SubscriptionEntitlementsResponse:
    if subscription is None:
        return SubscriptionEntitlementsResponse(
            active=False,
            features=[],
            limits=FREE_ENTITLEMENT_LIMITS,
        )
    plan = subscription.plan
    return SubscriptionEntitlementsResponse(
        active=True,
        current_period_end=subscription.current_period_end,
        features=list(plan.features_json),
        limits={
            "community_limit": plan.community_limit,
            "listing_limit": plan.listing_limit,
            "saved_search_limit": plan.saved_search_limit,
        },
        plan_id=plan.public_id,
        plan_slug=plan.slug,
        status=cast("SubscriptionStatus", subscription.status),
        subscription_id=subscription.public_id,
    )


def promotion_response(promotion: Promotion) -> PromotionResponse:
    paid_order = next((order for order in promotion.orders if order.status == "paid"), None)
    return PromotionResponse(
        id=promotion.public_id,
        is_paid=paid_order is not None,
        listing_id=promotion.listing.public_id,
        promotion_order_id=paid_order.public_id if paid_order is not None else None,
        seller_user_id=promotion.seller.public_id,
        type=cast("PromotionType", promotion.type),
        status=cast("PromotionStatus", promotion.status),
        amount_cents=promotion.amount_cents,
        currency=promotion.currency,
        starts_at=promotion.starts_at,
        ends_at=promotion.ends_at,
        created_at=promotion.created_at,
        updated_at=promotion.updated_at,
    )


def coupon_response(coupon: Coupon) -> CouponResponse:
    return CouponResponse(
        id=coupon.public_id,
        code=coupon.code,
        discount_type=cast("DiscountType", coupon.discount_type),
        discount_value=coupon.discount_value,
        min_order_cents=coupon.min_order_cents,
        max_uses=coupon.max_uses,
        used_count=coupon.used_count,
        valid_from=coupon.valid_from,
        valid_until=coupon.valid_until,
        is_active=coupon.is_active,
        created_at=coupon.created_at,
        updated_at=coupon.updated_at,
    )
