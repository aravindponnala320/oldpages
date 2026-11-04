from __future__ import annotations

from oldpages_api.identity.models import User
from oldpages_api.subscriptions.exceptions import ForbiddenSubscriptionActionError
from oldpages_api.subscriptions.models import Promotion, Subscription


def require_subscription_owner(subscription: Subscription, user: User) -> None:
    if subscription.user_id != user.id:
        raise ForbiddenSubscriptionActionError(
            "Only the subscription owner can perform this action."
        )


def require_promotion_owner(promotion: Promotion, user: User) -> None:
    if promotion.seller_user_id != user.id:
        raise ForbiddenSubscriptionActionError("Only the promotion owner can perform this action.")
