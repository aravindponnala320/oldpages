from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from oldpages_api.payments.schemas import (
    CartCheckoutRequest,
    CartCreateRequest,
    CartItemAddRequest,
    CartResponse,
    DisputeEvidenceRequest,
    DisputeOpenRequest,
    DisputeResolveRequest,
    DisputeResponse,
    OrderCancelRequest,
    OrderListResponse,
    OrderResponse,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PayoutResponse,
    RefundInitiateRequest,
    RefundResponse,
    ShipmentCreateRequest,
    ShipmentResponse,
    ShipmentStatusUpdateRequest,
)
from oldpages_api.payments.service import PaymentsService
from oldpages_api.shared.db.database import get_session

carts_router = APIRouter(prefix="/carts", tags=["carts"])
orders_router = APIRouter(prefix="/orders", tags=["orders"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])
shipments_router = APIRouter(prefix="/shipments", tags=["shipments"])
disputes_router = APIRouter(prefix="/disputes", tags=["disputes"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def payments_service(session: AsyncSession) -> PaymentsService:
    return PaymentsService(session)


# --- Carts ---


@carts_router.post("", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def create_cart(
    payload: CartCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> CartResponse:
    return await payments_service(session).create_cart(
        payload,
        principal.user,
        request_context(request),
    )


@carts_router.get("/{cart_id}", response_model=CartResponse)
async def get_cart(
    cart_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> CartResponse:
    from oldpages_api.payments.exceptions import CartNotFoundError
    from oldpages_api.payments.permissions import require_cart_owner
    from oldpages_api.payments.repository import PaymentsRepository
    from oldpages_api.payments.service import cart_response

    repo = PaymentsRepository(session)
    cart = await repo.get_cart_by_public_id(cart_id)
    if cart is None:
        raise CartNotFoundError()
    require_cart_owner(cart, principal.user)
    return cart_response(cart)


@carts_router.post("/{cart_id}/items", response_model=CartResponse)
async def add_cart_item(
    cart_id: str,
    payload: CartItemAddRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> CartResponse:
    return await payments_service(session).add_cart_item(cart_id, payload, principal.user)


@carts_router.delete("/{cart_id}/items/{item_id}", response_model=CartResponse)
async def remove_cart_item(
    cart_id: str,
    item_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> CartResponse:
    return await payments_service(session).remove_cart_item(cart_id, item_id, principal.user)


@carts_router.post("/{cart_id}/checkout", response_model=OrderResponse)
async def checkout_cart(
    cart_id: str,
    payload: CartCheckoutRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> OrderResponse:
    return await payments_service(session).checkout_cart(
        cart_id,
        payload,
        principal.user,
        request_context(request),
    )


# --- Orders ---


@orders_router.get("", response_model=OrderListResponse)
async def list_orders(
    principal: PrincipalDep,
    session: SessionDep,
    limit: int = 20,
    offset: int = 0,
) -> OrderListResponse:
    from oldpages_api.payments.repository import PaymentsRepository
    from oldpages_api.payments.service import order_response

    repo = PaymentsRepository(session)
    orders = await repo.list_orders_for_user(principal.user.id, limit=limit, offset=offset)
    return OrderListResponse(
        items=[order_response(o) for o in orders],
        total=len(orders),
    )


@orders_router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> OrderResponse:
    from oldpages_api.payments.exceptions import OrderNotFoundError
    from oldpages_api.payments.permissions import require_order_participant
    from oldpages_api.payments.repository import PaymentsRepository
    from oldpages_api.payments.service import order_response

    repo = PaymentsRepository(session)
    order = await repo.get_order_by_public_id(order_id)
    if order is None:
        raise OrderNotFoundError()
    require_order_participant(order, principal.user)
    return order_response(order)


@orders_router.post("/{order_id}/accept", response_model=OrderResponse)
async def accept_order(
    order_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> OrderResponse:
    return await payments_service(session).accept_order(
        order_id,
        principal.user,
        request_context(request),
    )


@orders_router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    payload: OrderCancelRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> OrderResponse:
    return await payments_service(session).cancel_order(
        order_id,
        payload,
        principal.user,
        request_context(request),
    )


# --- Payments ---


@payments_router.post(
    "/{order_id}/initiate",
    response_model=PaymentInitiateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_payment(
    order_id: str,
    payload: PaymentInitiateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> PaymentInitiateResponse:
    return await payments_service(session).initiate_payment(
        order_id,
        payload,
        principal.user,
        request_context(request),
    )


@payments_router.post("/webhook/{provider}")
async def payment_webhook(
    provider: str,
    request: Request,
    session: SessionDep,
) -> dict[str, str]:
    body = await request.body()
    signature = request.headers.get("x-webhook-signature", "")
    return await payments_service(session).handle_payment_webhook(provider, body, signature)


@payments_router.post("/{order_id}/refunds", response_model=RefundResponse)
async def initiate_refund(
    order_id: str,
    payload: RefundInitiateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> RefundResponse:
    return await payments_service(session).initiate_refund(
        order_id,
        payload,
        principal.user,
        request_context(request),
    )


@payments_router.post("/{order_id}/payouts", response_model=PayoutResponse)
async def initiate_payout(
    order_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> PayoutResponse:
    return await payments_service(session).initiate_payout(
        order_id,
        principal.user,
        request_context(request),
    )


# --- Shipments ---


@shipments_router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    payload: ShipmentCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ShipmentResponse:
    return await payments_service(session).create_shipment(
        payload,
        principal.user,
        request_context(request),
    )


@shipments_router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(
    shipment_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> ShipmentResponse:
    from oldpages_api.payments.exceptions import ShipmentNotFoundError
    from oldpages_api.payments.permissions import require_order_participant
    from oldpages_api.payments.repository import PaymentsRepository
    from oldpages_api.payments.service import shipment_response

    repo = PaymentsRepository(session)
    shipment = await repo.get_shipment_by_public_id(shipment_id)
    if shipment is None:
        raise ShipmentNotFoundError()
    require_order_participant(shipment.order, principal.user)
    return shipment_response(shipment)


@shipments_router.patch("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment_status(
    shipment_id: str,
    payload: ShipmentStatusUpdateRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> ShipmentResponse:
    return await payments_service(session).update_shipping_status(
        shipment_id,
        payload,
        principal.user,
    )


@shipments_router.post("/webhook/{provider}")
async def shipping_webhook(
    provider: str,
    request: Request,
    session: SessionDep,
) -> dict[str, str]:
    body = await request.body()
    signature = request.headers.get("x-webhook-signature", "")
    return await payments_service(session).handle_shipping_webhook(provider, body, signature)


# --- Disputes ---


@disputes_router.post("", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def open_dispute(
    payload: DisputeOpenRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> DisputeResponse:
    return await payments_service(session).open_dispute(
        payload,
        principal.user,
        request_context(request),
    )


@disputes_router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: str,
    principal: PrincipalDep,
    session: SessionDep,
) -> DisputeResponse:
    from oldpages_api.payments.exceptions import DisputeNotFoundError
    from oldpages_api.payments.permissions import require_dispute_participant
    from oldpages_api.payments.repository import PaymentsRepository
    from oldpages_api.payments.service import dispute_response

    repo = PaymentsRepository(session)
    dispute = await repo.get_dispute_by_public_id(dispute_id)
    if dispute is None:
        raise DisputeNotFoundError()
    require_dispute_participant(dispute, principal.user)
    return dispute_response(dispute)


@disputes_router.post("/{dispute_id}/evidence", response_model=DisputeResponse)
async def add_dispute_evidence(
    dispute_id: str,
    payload: DisputeEvidenceRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> DisputeResponse:
    return await payments_service(session).add_dispute_evidence(
        dispute_id,
        payload,
        principal.user,
    )


@disputes_router.post("/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(
    dispute_id: str,
    payload: DisputeResolveRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> DisputeResponse:
    return await payments_service(session).resolve_dispute(
        dispute_id,
        payload,
        principal.user,
        request_context(request),
    )
