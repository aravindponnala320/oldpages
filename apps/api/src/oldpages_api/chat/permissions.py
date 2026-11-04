from __future__ import annotations

from oldpages_api.chat.exceptions import ForbiddenChatActionError
from oldpages_api.chat.models import ChatRequest, Conversation
from oldpages_api.identity.models import User


def require_chat_request_recipient(actor: User, chat_request: ChatRequest) -> None:
    if actor.id != chat_request.recipient_user_id:
        raise ForbiddenChatActionError()


def require_conversation_member(actor: User, conversation: Conversation) -> None:
    if not any(
        member.user_id == actor.id and member.status in {"active", "muted", "archived"}
        for member in conversation.members
    ):
        raise ForbiddenChatActionError("Only conversation members can access this conversation.")
