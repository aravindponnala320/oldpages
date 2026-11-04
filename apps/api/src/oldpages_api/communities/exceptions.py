from __future__ import annotations

from oldpages_api.core.errors import AppError


class CommunityNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Community not found.",
            status_code=404,
            title="Community Not Found",
            type_uri="https://oldpages.in/problems/community-not-found",
        )


class CommunityPostNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Community post not found.",
            status_code=404,
            title="Community Post Not Found",
            type_uri="https://oldpages.in/problems/community-post-not-found",
        )


class ForbiddenCommunityActionError(AppError):
    def __init__(self, detail: str = "This community action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


class CommunityValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Community Request",
            type_uri="https://oldpages.in/problems/invalid-community-request",
        )


class InvalidCommunityStateTransitionError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Invalid Community State Transition",
            type_uri="https://oldpages.in/problems/invalid-community-state-transition",
        )
