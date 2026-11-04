from __future__ import annotations

from oldpages_api.core.errors import AppError


class ClubNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Book club not found.",
            status_code=404,
            title="Book Club Not Found",
            type_uri="https://oldpages.in/problems/book-club-not-found",
        )


class ClubBookNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Club book not found.",
            status_code=404,
            title="Club Book Not Found",
            type_uri="https://oldpages.in/problems/club-book-not-found",
        )


class EventNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Event not found.",
            status_code=404,
            title="Event Not Found",
            type_uri="https://oldpages.in/problems/event-not-found",
        )


class BuddyReadNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Buddy read not found.",
            status_code=404,
            title="Buddy Read Not Found",
            type_uri="https://oldpages.in/problems/buddy-read-not-found",
        )


class ForbiddenClubActionError(AppError):
    def __init__(self, detail: str = "This club action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


class ClubValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Club Request",
            type_uri="https://oldpages.in/problems/invalid-club-request",
        )


class InvalidClubStateTransitionError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Invalid Club State Transition",
            type_uri="https://oldpages.in/problems/invalid-club-state-transition",
        )
