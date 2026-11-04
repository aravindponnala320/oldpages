from __future__ import annotations

from oldpages_api.core.errors import AppError


class BusinessProfileNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Business profile not found.",
            status_code=404,
            title="Business Profile Not Found",
            type_uri="https://oldpages.in/problems/business-profile-not-found",
        )


class BusinessLocationNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Business location not found.",
            status_code=404,
            title="Business Location Not Found",
            type_uri="https://oldpages.in/problems/business-location-not-found",
        )


class StaffAccountNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Staff account not found.",
            status_code=404,
            title="Staff Account Not Found",
            type_uri="https://oldpages.in/problems/staff-account-not-found",
        )


class BusinessValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Business Request",
            type_uri="https://oldpages.in/problems/invalid-business-request",
        )


class AlreadyStaffError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="User is already a staff member of this business.",
            status_code=409,
            title="Already Staff",
            type_uri="https://oldpages.in/problems/already-staff",
        )


class ForbiddenBusinessActionError(AppError):
    def __init__(self, detail: str = "This business action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )
