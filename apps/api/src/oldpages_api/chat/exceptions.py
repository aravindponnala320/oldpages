from __future__ import annotations

from oldpages_api.core.errors import AppError


class ChatRequestNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Chat request not found.",
            status_code=404,
            title="Chat Request Not Found",
            type_uri="https://oldpages.in/problems/chat-request-not-found",
        )


class ConversationNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Conversation not found.",
            status_code=404,
            title="Conversation Not Found",
            type_uri="https://oldpages.in/problems/conversation-not-found",
        )


class ForbiddenChatActionError(AppError):
    def __init__(self, detail: str = "This chat action is not allowed.") -> None:
        super().__init__(
            detail=detail,
            status_code=403,
            title="Forbidden",
            type_uri="https://oldpages.in/problems/forbidden",
        )


class InvalidChatStateTransitionError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=409,
            title="Invalid Chat State Transition",
            type_uri="https://oldpages.in/problems/invalid-chat-state-transition",
        )


class ChatValidationError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            detail=detail,
            status_code=422,
            title="Invalid Chat Request",
            type_uri="https://oldpages.in/problems/invalid-chat-request",
        )
