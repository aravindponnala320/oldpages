from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.commerce.schemas import (
    CounterOfferRequest,
    EmptyActionRequest,
    OfferCreateRequest,
    OfferResponse,
    PickupConfirmRequest,
    PickupCreateRequest,
    PickupResponse,
    ReviewCreateRequest,
    ReviewResponse,
    TransactionCancelRequest,
    TransactionCompleteRequest,
    TransactionResponse,
)
from oldpages_api.commerce.service import CommerceService
from oldpages_api.commerce.service import CommerceService
from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from oldpages_api.shared.db.database import get_session

offers_router = APIRouter(prefix="/offers", tags=["offers"])
pickups_router = APIRouter(prefix="/pickups", tags=["pickups"])
transactions_router = APIRouter(prefix="/transactions", tags=["transactions"])
reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def commerce_service(session: AsyncSession) -> CommerceService:
    return CommerceService(session)


@offers_router.get("", response_model=list[OfferResponse])
async def list_offers(
    principal: PrincipalDep,
    session: SessionDep,
    role: str = Query(default="buyer"),
    listing_id: str | None = Query(default=None, max_length=26),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[OfferResponse]:
    return await commerce_service(session).list_offers(principal.user, role=role, listing_id=listing_id, limit=limit)


@offers_router.get("/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> OfferResponse:
    return await commerce_service(session).get_offer(offer_id, principal.user)


@offers_router.post("", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    payload: OfferCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> OfferResponse:
    return await commerce_service(session).create_offer(
        payload,
        principal.user,
        request_context(request),
    )


@offers_router.post("/{offer_id}/counter", response_model=OfferResponse)
async def counter_offer(
    offer_id: str,
    payload: CounterOfferRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> OfferResponse:
    return await commerce_service(session).counter_offer(
        offer_id,
        payload,
        principal.user,
        request_context(request),
    )


@offers_router.post("/{offer_id}/accept", response_model=OfferResponse)
async def accept_offer(
    offer_id: str,
    payload: EmptyActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> OfferResponse:
    return await commerce_service(session).accept_offer(
        offer_id,
        payload,
        principal.user,
        request_context(request),
    )


@offers_router.post("/{offer_id}/reject", response_model=OfferResponse)
async def reject_offer(
    offer_id: str,
    payload: EmptyActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> OfferResponse:
    return await commerce_service(session).reject_offer(
        offer_id,
        payload,
        principal.user,
        request_context(request),
    )


@offers_router.post("/{offer_id}/withdraw", response_model=OfferResponse)
async def withdraw_offer(
    offer_id: str,
    payload: EmptyActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> OfferResponse:
    return await commerce_service(session).withdraw_offer(
        offer_id,
        payload,
        principal.user,
        request_context(request),
    )


@pickups_router.post("", response_model=PickupResponse, status_code=status.HTTP_201_CREATED)
async def create_pickup(
    payload: PickupCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> PickupResponse:
    return await commerce_service(session).create_pickup(
        payload,
        principal.user,
        request_context(request),
    )


@pickups_router.post("/{pickup_id}/confirm", response_model=PickupResponse)
async def confirm_pickup(
    pickup_id: str,
    payload: PickupConfirmRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> PickupResponse:
    return await commerce_service(session).confirm_pickup(
        pickup_id,
        payload,
        principal.user,
        request_context(request),
    )


@transactions_router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    principal: PrincipalDep,
    session: SessionDep,
    role: str = Query(default="buyer"),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[TransactionResponse]:
    return await commerce_service(session).list_transactions(principal.user, role=role, limit=limit)


@transactions_router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> TransactionResponse:
    return await commerce_service(session).get_transaction(transaction_id, principal.user)


@transactions_router.post("/{transaction_id}/complete", response_model=TransactionResponse)
async def complete_transaction(
    transaction_id: str,
    payload: TransactionCompleteRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> TransactionResponse:
    return await commerce_service(session).complete_transaction(
        transaction_id,
        payload,
        principal.user,
        request_context(request),
    )


@transactions_router.post("/{transaction_id}/cancel", response_model=TransactionResponse)
async def cancel_transaction(
    transaction_id: str,
    payload: TransactionCancelRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> TransactionResponse:
    return await commerce_service(session).cancel_transaction(
        transaction_id, payload.reason, principal.user, request_context(request),
    )


@transactions_router.post("/{transaction_id}/mark-received", response_model=TransactionResponse)
async def mark_transaction_received(
    transaction_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> TransactionResponse:
    return await commerce_service(session).mark_transaction_received(
        transaction_id, principal.user, request_context(request),
    )


@transactions_router.post("/{transaction_id}/mark-delivered", response_model=TransactionResponse)
async def mark_transaction_delivered(
    transaction_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> TransactionResponse:
    return await commerce_service(session).mark_transaction_delivered(
        transaction_id, principal.user, request_context(request),
    )


@reviews_router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReviewResponse:
    return await commerce_service(session).create_review(
        payload,
        principal.user,
        request_context(request),
    )
