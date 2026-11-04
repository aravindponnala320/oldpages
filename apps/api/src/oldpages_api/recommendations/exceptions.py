from __future__ import annotations

from oldpages_api.core.errors import AppError


class RecommendationNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Recommendation not found.",
            status_code=404,
            title="Recommendation Not Found",
            type_uri="https://oldpages.in/problems/recommendation-not-found",
        )


class RecommendationValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Recommendation Request",
            type_uri="https://oldpages.in/problems/invalid-recommendation-request",
        )
