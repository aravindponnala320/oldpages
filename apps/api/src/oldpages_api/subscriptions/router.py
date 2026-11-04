from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import CurrentPrincipal, get_current_principal
from oldpages_api.shared.db.database import get_session
from oldpages_api.subscriptions.schemas import (
    CouponCreateRequest,
    CouponResponse,
    CouponValidateRequest,
    CouponValidateResponse,
    PromotionCreateRequest,
    PromotionResponse,
    SubscribeRequest,
    SubscriptionEntitlementsResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
)
from oldpages_api.subscriptions.service import SubscriptionService

plans_router = APIRouter(prefix="/subscription-plans", tags=["subscription-plans"])
subscriptions_router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
promotions_router = APIRouter(prefix="/promotions", tags=["promotions"])
coupons_router = APIRouter(prefix="/coupons", tags=["coupons"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def subscription_service(session: AsyncSession) -> SubscriptionService:
    return SubscriptionService(session)


@plans_router.get("", response_model=list[SubscriptionPlanResponse])
async def list_plans(session: SessionDep) -> list[SubscriptionPlanResponse]:
    return await subscription_service(session).list_plans()


@subscriptions_router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe(
    payload: SubscribeRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> SubscriptionResponse:
    return await subscription_service(session).subscribe(payload, principal.user)


@subscriptions_router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    principal: PrincipalDep,
    session: SessionDep,
) -> SubscriptionResponse:
    return await subscription_service(session).get_my_subscription(principal.user)


@subscriptions_router.get("/entitlements/me", response_model=SubscriptionEntitlementsResponse)
async def get_my_entitlements(
    principal: PrincipalDep,
    session: SessionDep,
) -> SubscriptionEntitlementsResponse:
    return await subscription_service(session).get_my_entitlements(principal.user)


@subscriptions_router.delete(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
)
async def cancel_subscription(
    subscription_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> SubscriptionResponse:
    return await subscription_service(session).cancel_subscription(subscription_id, principal.user)


@promotions_router.post(
    "",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_promotion(
    payload: PromotionCreateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> PromotionResponse:
    return await subscription_service(session).create_promotion(payload, principal.user)


@promotions_router.get("/me", response_model=list[PromotionResponse])
async def list_my_promotions(
    principal: PrincipalDep,
    session: SessionDep,
) -> list[PromotionResponse]:
    return await subscription_service(session).list_my_promotions(principal.user)


@promotions_router.delete(
    "/{promotion_id}",
    response_model=PromotionResponse,
)
async def cancel_promotion(
    promotion_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> PromotionResponse:
    return await subscription_service(session).cancel_promotion(promotion_id, principal.user)


@coupons_router.post(
    "",
    response_model=CouponResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_coupon(
    payload: CouponCreateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> CouponResponse:
    return await subscription_service(session).create_coupon(payload, principal.user)


@coupons_router.get("", response_model=list[CouponResponse])
async def list_coupons(
    principal: PrincipalDep,
    session: SessionDep,
) -> list[CouponResponse]:
    return await subscription_service(session).list_coupons(principal.user)


@coupons_router.post("/validate", response_model=CouponValidateResponse)
async def validate_coupon(
    payload: CouponValidateRequest,
    session: SessionDep,
) -> CouponValidateResponse:
    return await subscription_service(session).validate_coupon(payload)
