from __future__ import annotations

from oldpages_api.identity.models import User
from oldpages_api.payments.exceptions import ForbiddenPaymentsActionError
from oldpages_api.payments.models import Cart, Dispute, Order


def require_order_buyer(order: Order, user: User) -> None:
    if order.buyer_user_id != user.id:
        raise ForbiddenPaymentsActionError("Only the order buyer can perform this action.")


def require_order_seller(order: Order, user: User) -> None:
    if order.seller_user_id != user.id:
        raise ForbiddenPaymentsActionError("Only the order seller can perform this action.")


def require_order_participant(order: Order, user: User) -> None:
    if user.id not in {order.buyer_user_id, order.seller_user_id}:
        raise ForbiddenPaymentsActionError("Only order participants can access this order.")


def require_cart_owner(cart: Cart, user: User) -> None:
    if cart.buyer_user_id != user.id:
        raise ForbiddenPaymentsActionError("Only the cart owner can access this cart.")


def require_dispute_participant(dispute: Dispute, user: User) -> None:
    if user.id not in {dispute.order.buyer_user_id, dispute.order.seller_user_id}:
        raise ForbiddenPaymentsActionError("Only order participants can access this dispute.")
