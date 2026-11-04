from __future__ import annotations

from oldpages_api.core.errors import AppError


class InstitutionNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Institution not found.",
            status_code=404,
            title="Institution Not Found",
            type_uri="https://oldpages.in/problems/institution-not-found",
        )


class InstitutionMemberNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Institution member not found.",
            status_code=404,
            title="Institution Member Not Found",
            type_uri="https://oldpages.in/problems/institution-member-not-found",
        )


class InstitutionValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Institution Request",
            type_uri="https://oldpages.in/problems/invalid-institution-request",
        )


class AlreadyMemberError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="User is already a member of this institution.",
            status_code=409,
            title="Already Member",
            type_uri="https://oldpages.in/problems/already-institution-member",
        )


class ForbiddenInstitutionActionError(AppError):
    def __init__(self, detail: str = "This institution action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )
