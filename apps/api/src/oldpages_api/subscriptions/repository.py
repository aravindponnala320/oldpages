from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.subscriptions.models import (
    Coupon,
    Promotion,
    Subscription,
    SubscriptionPlan,
)


class SubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # Plans
    async def get_plan_by_id(self, plan_id: int) -> SubscriptionPlan | None:
        result = await self.session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_plan_by_public_id(self, public_id: str) -> SubscriptionPlan | None:
        result = await self.session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def list_plans(self) -> list[SubscriptionPlan]:
        result = await self.session.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.sort_order.asc(), SubscriptionPlan.id.asc())
        )
        return list(result.scalars().all())

    # Subscriptions
    async def get_subscription_by_public_id(self, public_id: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .execution_options(populate_existing=True)
            .options(*subscription_load_options())
            .where(Subscription.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_active_subscription_for_user(self, user_id: int) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .execution_options(populate_existing=True)
            .options(*subscription_load_options())
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["active", "trialing"]),
            )
            .order_by(Subscription.id.desc())
            .limit(1)
        )
        return result.unique().scalar_one_or_none()

    async def list_subscriptions_for_user(self, user_id: int) -> list[Subscription]:
        result = await self.session.execute(
            select(Subscription)
            .options(*subscription_load_options())
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.id.desc())
        )
        return list(result.unique().scalars().all())

    # Promotions
    async def get_promotion_by_public_id(self, public_id: str) -> Promotion | None:
        result = await self.session.execute(
            select(Promotion)
            .execution_options(populate_existing=True)
            .options(*promotion_load_options())
            .where(Promotion.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_promotions_for_seller(self, seller_user_id: int) -> list[Promotion]:
        result = await self.session.execute(
            select(Promotion)
            .options(*promotion_load_options())
            .where(Promotion.seller_user_id == seller_user_id)
            .order_by(Promotion.id.desc())
        )
        return list(result.unique().scalars().all())

    # Coupons
    async def get_coupon_by_code(self, code: str) -> Coupon | None:
        result = await self.session.execute(select(Coupon).where(Coupon.code == code))
        return result.scalar_one_or_none()

    async def get_coupon_by_public_id(self, public_id: str) -> Coupon | None:
        result = await self.session.execute(select(Coupon).where(Coupon.public_id == public_id))
        return result.scalar_one_or_none()

    async def list_coupons(self) -> list[Coupon]:
        result = await self.session.execute(select(Coupon).order_by(Coupon.id.desc()))
        return list(result.scalars().all())

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def subscription_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Subscription.plan),
        selectinload(Subscription.user),
    )


def promotion_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Promotion.listing),
        selectinload(Promotion.orders),
        selectinload(Promotion.seller),
    )


__all__ = ["SubscriptionRepository"]
