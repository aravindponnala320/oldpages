from __future__ import annotations

from oldpages_api.core.errors import AppError


class SearchValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Search Request",
            type_uri="https://oldpages.in/problems/invalid-search-request",
        )


class SearchResourceNotFoundError(AppError):
    def __init__(self, detail: str = "Search resource not found.") -> None:
        super().__init__(
            detail=detail,
            status_code=404,
            title="Search Resource Not Found",
            type_uri="https://oldpages.in/problems/search-resource-not-found",
        )


class DuplicateSearchResourceError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Duplicate Search Resource",
            type_uri="https://oldpages.in/problems/duplicate-search-resource",
        )


class ForbiddenSearchActionError(AppError):
    def __init__(self, detail: str = "This search action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )
