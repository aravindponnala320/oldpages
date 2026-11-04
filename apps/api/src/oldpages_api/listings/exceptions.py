from __future__ import annotations

from oldpages_api.core.errors import AppError


class ListingNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Listing not found.",
            status_code=404,
            title="Listing Not Found",
            type_uri="https://oldpages.in/problems/listing-not-found",
        )


class MediaAssetNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Media asset not found.",
            status_code=404,
            title="Media Asset Not Found",
            type_uri="https://oldpages.in/problems/media-asset-not-found",
        )


class ForbiddenListingActionError(AppError):
    def __init__(self, detail: str = "This listing action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


class InvalidListingStateTransitionError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Invalid Listing State Transition",
            type_uri="https://oldpages.in/problems/invalid-listing-state-transition",
        )


class ListingValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Listing",
            type_uri="https://oldpages.in/problems/invalid-listing",
        )


class MediaValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Media Upload",
            type_uri="https://oldpages.in/problems/invalid-media-upload",
        )
