from __future__ import annotations

from oldpages_api.core.errors import AppError


class ReadingNotFoundError(AppError):
    def __init__(self, detail: str = "Reading resource was not found.") -> None:
        super().__init__(
            detail=detail,
            status_code=404,
            title="Reading Resource Not Found",
            type_uri="https://oldpages.in/problems/reading-not-found",
        )


class ReadingValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Reading Request",
            type_uri="https://oldpages.in/problems/invalid-reading-request",
        )


class ForbiddenReadingActionError(AppError):
    def __init__(self, detail: str = "This reading action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden Reading Action",
            type_uri="https://oldpages.in/problems/forbidden-reading-action",
        )


__all__ = [
    "ForbiddenReadingActionError",
    "ReadingNotFoundError",
    "ReadingValidationError",
]
