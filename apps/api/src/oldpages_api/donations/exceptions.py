from __future__ import annotations

from oldpages_api.core.errors import AppError


class CampaignNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Donation campaign not found.",
            status_code=404,
            title="Campaign Not Found",
            type_uri="https://oldpages.in/problems/campaign-not-found",
        )


class PledgeNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Donation pledge not found.",
            status_code=404,
            title="Pledge Not Found",
            type_uri="https://oldpages.in/problems/pledge-not-found",
        )


class DonationValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Donation Request",
            type_uri="https://oldpages.in/problems/invalid-donation-request",
        )


class ForbiddenDonationActionError(AppError):
    def __init__(self, detail: str = "This donation action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )
