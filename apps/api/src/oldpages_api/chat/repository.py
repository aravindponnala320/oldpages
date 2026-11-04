from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.chat.models import (
    ChatRequest,
    Conversation,
    ConversationMember,
    Message,
    MessageAttachment,
    MessageRead,
    MessageReport,
)
from oldpages_api.identity.models import User, UserBlock, UserProfile
from oldpages_api.listings.models import Listing, MediaAsset


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_listing_by_public_id(self, public_id: str) -> Listing | None:
        result = await self.session.execute(
            select(Listing)
            .options(selectinload(Listing.seller))
            .where(Listing.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_chat_request_by_public_id(self, public_id: str) -> ChatRequest | None:
        result = await self.session.execute(
            select(ChatRequest)
            .execution_options(populate_existing=True)
            .options(*chat_request_load_options())
            .where(ChatRequest.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_existing_chat_request(
        self,
        requester_user_id: int,
        recipient_user_id: int,
        listing_id: int,
    ) -> ChatRequest | None:
        result = await self.session.execute(
            select(ChatRequest)
            .options(*chat_request_load_options())
            .where(
                ChatRequest.requester_user_id == requester_user_id,
                ChatRequest.recipient_user_id == recipient_user_id,
                ChatRequest.listing_id == listing_id,
                ChatRequest.status.in_(["pending", "accepted"]),
            )
            .order_by(ChatRequest.created_at.desc(), ChatRequest.id.desc())
        )
        return result.unique().scalars().first()

    async def get_conversation_by_public_id(self, public_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation)
            .execution_options(populate_existing=True)
            .options(*conversation_load_options())
            .where(Conversation.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: int,
        *,
        cursor: str | None,
        limit: int,
        listing_db_id: int | None = None,
    ) -> tuple[list[Conversation], str | None]:
        stmt = (
            select(Conversation)
            .join(ConversationMember)
            .options(*conversation_load_options())
            .where(
                ConversationMember.user_id == user_id,
                ConversationMember.status.in_(["active", "muted", "archived"]),
            )
            .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc())
            .limit(limit + 1)
        )
        if listing_db_id is not None:
            stmt = stmt.where(Conversation.listing_id == listing_db_id)
        if cursor:
            cursor_conversation = await self.get_conversation_by_public_id(cursor)
            if cursor_conversation is not None:
                stmt = stmt.where(Conversation.id < cursor_conversation.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def list_messages(
        self,
        conversation_id: int,
        *,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Message], str | None]:
        stmt = (
            select(Message)
            .options(*message_load_options())
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .limit(limit + 1)
        )
        if cursor:
            cursor_message = await self.get_message_by_public_id(cursor)
            if cursor_message is not None:
                stmt = stmt.where(Message.id > cursor_message.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def list_messages_after(
        self, user_id: int, last_message_public_id: str | None
    ) -> list[Message]:
        member_conversation_ids = select(ConversationMember.conversation_id).where(
            ConversationMember.user_id == user_id,
            ConversationMember.status.in_(["active", "muted", "archived"]),
        )
        stmt = (
            select(Message)
            .options(*message_load_options())
            .where(Message.conversation_id.in_(member_conversation_ids))
            .order_by(Message.created_at.asc(), Message.id.asc())
            .limit(50)
        )
        if last_message_public_id:
            last_message = await self.get_message_by_public_id(last_message_public_id)
            if last_message is not None:
                stmt = stmt.where(Message.id > last_message.id)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_message_by_public_id(self, public_id: str) -> Message | None:
        result = await self.session.execute(
            select(Message).options(*message_load_options()).where(Message.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_message_by_client_id(
        self,
        conversation_id: int,
        sender_user_id: int,
        client_message_id: str,
    ) -> Message | None:
        result = await self.session.execute(
            select(Message)
            .options(*message_load_options())
            .where(
                Message.conversation_id == conversation_id,
                Message.sender_user_id == sender_user_id,
                Message.client_message_id == client_message_id,
            )
        )
        return result.unique().scalar_one_or_none()

    async def get_media_by_public_id(self, public_id: str) -> MediaAsset | None:
        result = await self.session.execute(
            select(MediaAsset).where(MediaAsset.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.public_id == public_id))
        return result.scalar_one_or_none()

    async def has_block_between(self, first_user_id: int, second_user_id: int) -> bool:
        result = await self.session.execute(
            select(UserBlock.id).where(
                or_(
                    (
                        (UserBlock.blocker_user_id == first_user_id)
                        & (UserBlock.blocked_user_id == second_user_id)
                    ),
                    (
                        (UserBlock.blocker_user_id == second_user_id)
                        & (UserBlock.blocked_user_id == first_user_id)
                    ),
                )
            )
        )
        return result.first() is not None

    async def get_message_report(
        self, message_id: int, reporter_user_id: int
    ) -> MessageReport | None:
        result = await self.session.execute(
            select(MessageReport).where(
                MessageReport.message_id == message_id,
                MessageReport.reporter_user_id == reporter_user_id,
            )
        )
        return result.scalar_one_or_none()

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def list_chat_requests_for_user(
        self,
        user_id: int,
        role: str = "recipient",
        status: str | None = None,
        limit: int = 50,
    ) -> list[ChatRequest]:
        if role == "recipient":
            condition = ChatRequest.recipient_user_id == user_id
        else:
            condition = ChatRequest.requester_user_id == user_id
        stmt = (
            select(ChatRequest)
            .options(*chat_request_load_options())
            .where(condition)
            .order_by(ChatRequest.created_at.desc())
            .limit(limit)
        )
        if status:
            stmt = stmt.where(ChatRequest.status == status)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def commit(self) -> None:
        await self.session.commit()


def chat_request_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(ChatRequest.conversation).selectinload(Conversation.members),
        selectinload(ChatRequest.listing),
        selectinload(ChatRequest.recipient).selectinload(User.profile),
        selectinload(ChatRequest.requester).selectinload(User.profile),
    )


def conversation_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Conversation.listing),
        selectinload(Conversation.members)
        .selectinload(ConversationMember.user)
        .selectinload(User.profile),
        selectinload(Conversation.messages)
        .selectinload(Message.reads)
        .selectinload(MessageRead.user),
    )


def message_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Message.attachments).selectinload(MessageAttachment.media_asset),
        selectinload(Message.conversation),
        selectinload(Message.listing),
        selectinload(Message.reads).selectinload(MessageRead.user),
        selectinload(Message.sender),
    )


__all__ = [
    "ChatRepository",
    "ChatRequest",
    "Conversation",
    "ConversationMember",
    "Message",
    "MessageAttachment",
    "MessageRead",
    "MessageReport",
]
