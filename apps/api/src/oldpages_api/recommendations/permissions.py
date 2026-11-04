from __future__ import annotations

from oldpages_api.identity.models import User
from oldpages_api.recommendations.exceptions import RecommendationNotFoundError
from oldpages_api.recommendations.models import Recommendation


def require_recommendation_owner(recommendation: Recommendation, user: User) -> None:
    if recommendation.user_id != user.id:
        raise RecommendationNotFoundError()
