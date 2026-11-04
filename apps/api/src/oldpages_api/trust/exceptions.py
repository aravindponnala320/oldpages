from __future__ import annotations

from oldpages_api.core.errors import AppError


class ReportNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Report not found.",
            status_code=404,
            title="Report Not Found",
            type_uri="https://oldpages.in/problems/report-not-found",
        )


class ModerationCaseNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Moderation case not found.",
            status_code=404,
            title="Moderation Case Not Found",
            type_uri="https://oldpages.in/problems/moderation-case-not-found",
        )


class ForbiddenTrustActionError(AppError):
    def __init__(self, detail: str = "This trust and safety action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


class InvalidTrustStateTransitionError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Invalid Trust State Transition",
            type_uri="https://oldpages.in/problems/invalid-trust-state-transition",
        )


class TrustValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Trust Request",
            type_uri="https://oldpages.in/problems/invalid-trust-request",
        )
