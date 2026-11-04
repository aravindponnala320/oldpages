from __future__ import annotations

from oldpages_api.core.errors import AppError


class DuplicateAccountError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="An account with that email already exists.",
            status_code=409,
            title="Account Already Exists",
            type_uri="https://oldpages.in/problems/account-exists",
        )


class InvalidCredentialsError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Invalid email or password.",
            status_code=401,
            title="Invalid Credentials",
            type_uri="https://oldpages.in/problems/invalid-credentials",
        )


class InvalidTokenError(AppError):
    def __init__(self, detail: str = "Invalid or expired token.") -> None:
        super().__init__(
            detail=detail,
            status_code=401,
            title="Invalid Token",
            type_uri="https://oldpages.in/problems/invalid-token",
        )


class RefreshTokenReuseError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Refresh token reuse was detected and the session was revoked.",
            status_code=401,
            title="Refresh Token Reuse Detected",
            type_uri="https://oldpages.in/problems/refresh-token-reuse",
        )


class UnauthorizedError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Authentication is required.",
            status_code=401,
            title="Unauthorized",
            type_uri="https://oldpages.in/problems/unauthorized",
        )


class ForbiddenIdentityActionError(AppError):
    def __init__(self, detail: str = "This identity action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


class UserNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="User not found.",
            status_code=404,
            title="User Not Found",
            type_uri="https://oldpages.in/problems/user-not-found",
        )
