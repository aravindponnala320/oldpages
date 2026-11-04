from __future__ import annotations

from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.chat.events import (
    CHAT_ACCEPTED,
    CHAT_DECLINED,
    CHAT_REQUEST_BLOCKED,
    CHAT_REQUESTED,
    CONVERSATION_READ,
    MESSAGE_SENT,
)
from oldpages_api.chat.exceptions import (
    ChatRequestNotFoundError,
    ChatValidationError,
    ConversationNotFoundError,
    ForbiddenChatActionError,
    InvalidChatStateTransitionError,
)
from oldpages_api.chat.models import (
    ChatRequest,
    Conversation,
    ConversationMember,
    Message,
    MessageAttachment,
    MessageRead,
    MessageReport,
)
from oldpages_api.chat.permissions import (
    require_chat_request_recipient,
    require_conversation_member,
)
from oldpages_api.chat.repository import ChatRepository
from oldpages_api.chat.schemas import (
    AttachmentType,
    ChatRequestActionRequest,
    ChatRequestCreateRequest,
    ChatRequestResponse,
    ChatRequestStatus,
    ConversationListResponse,
    ConversationMemberResponse,
    ConversationMemberRole,
    ConversationMemberStatus,
    ConversationResponse,
    ConversationStatus,
    MessageAttachmentResponse,
    MessageCreateRequest,
    MessageListResponse,
    MessageReportRequest,
    MessageReportResponse,
    MessageResponse,
    MessageType,
    UserSummary,
)
from oldpages_api.chat.tasks import publish_realtime_event
from oldpages_api.identity.models import AuditLog, User, UserBlock
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.listings.models import MediaAsset
from oldpages_api.notifications.service import NotificationService


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ChatRepository(session)
        self.notifications = NotificationService(session)

    async def list_chat_requests(
        self,
        actor: User,
        role: str = "recipient",
        status: str | None = None,
        limit: int = 50,
    ) -> list[ChatRequestResponse]:
        requests = await self.repo.list_chat_requests_for_user(
            actor.id, role=role, status=status, limit=limit
        )
        return [chat_request_response(r) for r in requests]

    async def create_chat_request(
        self,
        payload: ChatRequestCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ChatRequestResponse:
        listing = await self.repo.get_listing_by_public_id(payload.listing_id)
        if listing is None or listing.status != "active":
            raise ChatValidationError("Chat requests can only target active listings.")
        if listing.seller_user_id == actor.id:
            raise ForbiddenChatActionError("Sellers cannot request chat on their own listing.")
        if await self.repo.has_block_between(actor.id, listing.seller_user_id):
            raise ForbiddenChatActionError("Blocked users cannot initiate chat.")
        existing = await self.repo.get_existing_chat_request(
            actor.id,
            listing.seller_user_id,
            listing.id,
        )
        if existing is not None:
            return chat_request_response(existing)

        chat_request = ChatRequest(
            initial_message=payload.message,
            listing_id=listing.id,
            recipient_user_id=listing.seller_user_id,
            requester_user_id=actor.id,
            status="pending",
        )
        self.repo.add(chat_request)
        await self.repo.flush()
        await self.notifications.create_notification(
            body=payload.message or "A buyer wants to chat about your listing.",
            notification_type="chat_request",
            related_entity_id=chat_request.public_id,
            related_entity_type="chat_request",
            title="New chat request",
            user_id=listing.seller_user_id,
            data={"listing_id": listing.public_id, "requester_id": actor.public_id},
        )
        await self.audit(
            action=CHAT_REQUESTED,
            actor=actor,
            context=context,
            payload={"chat_request_id": chat_request.public_id, "listing_id": listing.public_id},
            target_user_id=listing.seller_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_chat_request_model(chat_request.public_id)
        return chat_request_response(reloaded)

    async def accept_chat_request(
        self,
        request_id: str,
        payload: ChatRequestActionRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ChatRequestResponse:
        chat_request = await self.get_chat_request_model(request_id)
        require_chat_request_recipient(actor, chat_request)
        if chat_request.status == "accepted" and chat_request.conversation is not None:
            return chat_request_response(chat_request)
        if chat_request.status != "pending":
            raise InvalidChatStateTransitionError("Only pending chat requests can be accepted.")
        if await self.repo.has_block_between(chat_request.requester_user_id, actor.id):
            raise ForbiddenChatActionError("Blocked users cannot start conversations.")

        conversation = Conversation(
            listing_id=chat_request.listing_id,
            status="active",
        )
        self.repo.add(conversation)
        await self.repo.flush()
        self.repo.add(
            ConversationMember(
                conversation_id=conversation.id,
                role="requester",
                status="active",
                user_id=chat_request.requester_user_id,
            )
        )
        self.repo.add(
            ConversationMember(
                conversation_id=conversation.id,
                role="recipient",
                status="active",
                user_id=chat_request.recipient_user_id,
            )
        )
        chat_request.conversation_id = conversation.id
        chat_request.conversation = conversation
        chat_request.response_message = payload.message
        chat_request.responded_at = utc_now()
        chat_request.status = "accepted"
        await self.notifications.create_notification(
            body=payload.message or "Your chat request was accepted.",
            notification_type="chat_accepted",
            related_entity_id=conversation.public_id,
            related_entity_type="conversation",
            title="Chat request accepted",
            user_id=chat_request.requester_user_id,
            data={"chat_request_id": chat_request.public_id},
        )
        await self.audit(
            action=CHAT_ACCEPTED,
            actor=actor,
            context=context,
            payload={"chat_request_id": chat_request.public_id},
            target_user_id=chat_request.requester_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_chat_request_model(chat_request.public_id)
        return chat_request_response(reloaded)

    async def decline_chat_request(
        self,
        request_id: str,
        payload: ChatRequestActionRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ChatRequestResponse:
        chat_request = await self.get_chat_request_model(request_id)
        require_chat_request_recipient(actor, chat_request)
        if chat_request.status != "pending":
            raise InvalidChatStateTransitionError("Only pending chat requests can be declined.")
        chat_request.response_message = payload.message
        chat_request.responded_at = utc_now()
        chat_request.status = "declined"
        await self.notifications.create_notification(
            body=payload.message or "Your chat request was declined.",
            notification_type="chat_declined",
            related_entity_id=chat_request.public_id,
            related_entity_type="chat_request",
            title="Chat request declined",
            user_id=chat_request.requester_user_id,
            data={"chat_request_id": chat_request.public_id},
        )
        await self.audit(
            action=CHAT_DECLINED,
            actor=actor,
            context=context,
            payload={"chat_request_id": chat_request.public_id},
            target_user_id=chat_request.requester_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_chat_request_model(chat_request.public_id)
        return chat_request_response(reloaded)

    async def block_chat_request(
        self,
        request_id: str,
        payload: ChatRequestActionRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ChatRequestResponse:
        chat_request = await self.get_chat_request_model(request_id)
        require_chat_request_recipient(actor, chat_request)
        if chat_request.status not in {"pending", "declined"}:
            raise InvalidChatStateTransitionError(
                "Only pending or declined requests can be blocked."
            )
        chat_request.response_message = payload.message
        chat_request.responded_at = utc_now()
        chat_request.status = "blocked"
        if not await self.repo.has_block_between(actor.id, chat_request.requester_user_id):
            self.repo.add(
                UserBlock(
                    blocker_user_id=actor.id,
                    blocked_user_id=chat_request.requester_user_id,
                    reason=payload.message,
                )
            )
        await self.audit(
            action=CHAT_REQUEST_BLOCKED,
            actor=actor,
            context=context,
            payload={"chat_request_id": chat_request.public_id},
            target_user_id=chat_request.requester_user_id,
        )
        await self.repo.commit()
        reloaded = await self.get_chat_request_model(chat_request.public_id)
        return chat_request_response(reloaded)

    async def list_conversations(
        self,
        actor: User,
        *,
        cursor: str | None,
        limit: int,
        listing_id: str | None = None,
    ) -> ConversationListResponse:
        listing_db_id: int | None = None
        if listing_id:
            from sqlalchemy import select as sa_select
            from oldpages_api.listings.models import Listing
            res = await self.repo.session.execute(
                sa_select(Listing.id).where(Listing.public_id == listing_id)
            )
            listing_db_id = res.scalar_one_or_none()
        conversations, next_cursor = await self.repo.list_conversations(
            actor.id,
            cursor=cursor,
            limit=limit,
            listing_db_id=listing_db_id,
        )
        return ConversationListResponse(
            items=[conversation_response(item, actor.id) for item in conversations],
            next_cursor=next_cursor,
        )

    async def list_messages(
        self,
        conversation_id: str,
        actor: User,
        *,
        cursor: str | None,
        limit: int,
        context: AuthenticatedRequestContext,
    ) -> MessageListResponse:
        conversation = await self.get_conversation_model(conversation_id)
        require_conversation_member(actor, conversation)
        messages, next_cursor = await self.repo.list_messages(
            conversation.id,
            cursor=cursor,
            limit=limit,
        )
        await self.mark_messages_read(conversation, messages, actor, context)
        await self.repo.commit()
        reloaded_messages, _next = await self.repo.list_messages(
            conversation.id,
            cursor=cursor,
            limit=limit,
        )
        return MessageListResponse(
            items=[message_response(item) for item in reloaded_messages],
            next_cursor=next_cursor,
        )

    async def send_message(
        self,
        conversation_id: str,
        payload: MessageCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> MessageResponse:
        conversation = await self.get_conversation_model(conversation_id)
        require_conversation_member(actor, conversation)
        if conversation.status != "active":
            raise InvalidChatStateTransitionError(
                "Messages can only be sent to active conversations."
            )
        existing = await self.repo.get_message_by_client_id(
            conversation.id,
            actor.id,
            payload.client_message_id,
        )
        if existing is not None:
            return message_response(existing)

        listing = None
        if payload.listing_id is not None:
            listing = await self.repo.get_listing_by_public_id(payload.listing_id)
            if listing is None:
                raise ChatValidationError("Listing card target not found.")
        message = Message(
            body=payload.body,
            client_message_id=payload.client_message_id,
            conversation_id=conversation.id,
            listing_id=listing.id if listing is not None else None,
            message_type=payload.message_type,
            metadata_json=payload.metadata,
            sender_user_id=actor.id,
        )
        self.repo.add(message)
        await self.repo.flush()
        for index, attachment in enumerate(payload.attachments):
            media = await self.repo.get_media_by_public_id(attachment.media_id)
            valid_media = validate_message_media(media, actor)
            self.repo.add(
                MessageAttachment(
                    attachment_type=attachment.attachment_type,
                    media_asset_id=valid_media.id,
                    message_id=message.id,
                    metadata_json=attachment.metadata,
                    sort_order=index,
                )
            )
        now = utc_now()
        conversation.last_message_at = now
        self.repo.add(MessageRead(message_id=message.id, read_at=now, user_id=actor.id))
        for member in conversation.members:
            if member.user_id == actor.id or member.status == "blocked":
                continue
            await self.notifications.create_notification(
                body=message_preview(payload),
                notification_type="message",
                related_entity_id=conversation.public_id,
                related_entity_type="conversation",
                title="New message",
                user_id=member.user_id,
                data={
                    "conversation_id": conversation.public_id,
                    "message_client_id": payload.client_message_id,
                },
            )
        await self.audit(
            action=MESSAGE_SENT,
            actor=actor,
            context=context,
            payload={"conversation_id": conversation.public_id, "message_id": message.public_id},
            target_user_id=None,
        )
        await self.repo.commit()
        reloaded = await self.repo.get_message_by_public_id(message.public_id)
        if reloaded is None:
            raise ConversationNotFoundError()
        resp = message_response(reloaded)
        await publish_realtime_event(
            conversation.public_id,
            "message.created",
            {"message": resp.model_dump(mode="json")},
        )
        return resp

    async def report_message(
        self,
        message_id: str,
        payload: MessageReportRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> MessageReportResponse:
        message = await self.repo.get_message_by_public_id(message_id)
        if message is None:
            raise ConversationNotFoundError()
        conversation = await self.get_conversation_model(message.conversation.public_id)
        require_conversation_member(actor, conversation)
        existing = await self.repo.get_message_report(message.id, actor.id)
        if existing is not None:
            return message_report_response(existing, message.public_id)
        report = MessageReport(
            details=payload.details,
            message_id=message.id,
            reason=payload.reason,
            reporter_user_id=actor.id,
            status="open",
        )
        self.repo.add(report)
        await self.audit(
            action="MESSAGE_REPORTED",
            actor=actor,
            context=context,
            payload={"message_id": message.public_id, "reason": payload.reason},
            target_user_id=message.sender_user_id,
        )
        await self.repo.commit()
        return message_report_response(report, message.public_id)

    async def websocket_replay(
        self,
        actor: User,
        last_message_id: str | None,
    ) -> list[MessageResponse]:
        messages = await self.repo.list_messages_after(actor.id, last_message_id)
        return [message_response(item) for item in messages]

    async def get_chat_request_model(self, request_id: str) -> ChatRequest:
        chat_request = await self.repo.get_chat_request_by_public_id(request_id)
        if chat_request is None:
            raise ChatRequestNotFoundError()
        return chat_request

    async def get_conversation_model(self, conversation_id: str) -> Conversation:
        conversation = await self.repo.get_conversation_by_public_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError()
        return conversation

    async def mark_messages_read(
        self,
        conversation: Conversation,
        messages: list[Message],
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> None:
        existing_reads = {
            read.message_id
            for message in messages
            for read in message.reads
            if read.user_id == actor.id
        }
        now = utc_now()
        last_read_message_id = None
        for message in messages:
            if message.sender_user_id == actor.id or message.id in existing_reads:
                continue
            self.repo.add(MessageRead(message_id=message.id, read_at=now, user_id=actor.id))
            last_read_message_id = message.id
        if last_read_message_id is not None:
            for member in conversation.members:
                if member.user_id == actor.id:
                    member.last_read_at = now
                    member.last_read_message_id = last_read_message_id
                    break
            await self.audit(
                action=CONVERSATION_READ,
                actor=actor,
                context=context,
                payload={"conversation_id": conversation.public_id},
                target_user_id=None,
            )

    async def audit(
        self,
        *,
        action: str,
        actor: User,
        context: AuthenticatedRequestContext,
        payload: dict[str, str],
        target_user_id: int | None,
    ) -> None:
        self.repo.add(
            AuditLog(
                action=action,
                actor_user_id=actor.id,
                context_json=payload,
                ip_address=context.ip_address,
                target_user_id=target_user_id,
                user_agent=context.user_agent,
            )
        )


def validate_message_media(media: MediaAsset | None, actor: User) -> MediaAsset:
    if media is None:
        raise ChatValidationError("Message attachment media not found.")
    if media.user_id != actor.id:
        raise ForbiddenChatActionError("Only the media owner can attach a media asset.")
    if media.status not in {"uploaded", "approved"}:
        raise ChatValidationError("Only uploaded or approved media can be attached.")
    return media


def message_preview(payload: MessageCreateRequest) -> str:
    if payload.body:
        return payload.body[:160]
    if payload.message_type == "image":
        return "Sent an image."
    if payload.message_type == "listing":
        return "Sent a listing."
    return "Sent a message."


def chat_request_response(chat_request: ChatRequest) -> ChatRequestResponse:
    requester_name = None
    if hasattr(chat_request.requester, "profile") and chat_request.requester.profile:
        requester_name = chat_request.requester.profile.display_name
    recipient_name = None
    if hasattr(chat_request.recipient, "profile") and chat_request.recipient.profile:
        recipient_name = chat_request.recipient.profile.display_name
    listing_title = None
    if chat_request.listing and hasattr(chat_request.listing, "title_snapshot"):
        listing_title = chat_request.listing.title_snapshot
    return ChatRequestResponse(
        conversation_id=chat_request.conversation.public_id if chat_request.conversation else None,
        created_at=chat_request.created_at,
        id=chat_request.public_id,
        initial_message=chat_request.initial_message,
        listing_id=chat_request.listing.public_id,
        listing_title=listing_title,
        recipient=UserSummary(id=chat_request.recipient.public_id, display_name=recipient_name),
        requester=UserSummary(id=chat_request.requester.public_id, display_name=requester_name),
        responded_at=chat_request.responded_at,
        response_message=chat_request.response_message,
        status=cast("ChatRequestStatus", chat_request.status),
    )


def conversation_response(conversation: Conversation, actor_user_id: int) -> ConversationResponse:
    listing_title = None
    if conversation.listing and hasattr(conversation.listing, "title_snapshot"):
        listing_title = conversation.listing.title_snapshot

    last_preview: str | None = None
    if conversation.messages:
        sorted_msgs = sorted(conversation.messages, key=lambda m: m.created_at, reverse=True)
        latest = sorted_msgs[0]
        last_preview = latest.body[:80] if latest.body else "📎 Attachment"

    members_resp = []
    for member in sorted(conversation.members, key=lambda item: item.role):
        display_name = None
        if hasattr(member.user, "profile") and member.user.profile:
            display_name = member.user.profile.display_name
        members_resp.append(ConversationMemberResponse(
            role=cast("ConversationMemberRole", member.role),
            status=cast("ConversationMemberStatus", member.status),
            user=UserSummary(id=member.user.public_id, display_name=display_name),
        ))

    return ConversationResponse(
        created_at=conversation.created_at,
        id=conversation.public_id,
        last_message_at=conversation.last_message_at,
        last_message_preview=last_preview,
        listing_id=conversation.listing.public_id if conversation.listing else None,
        listing_title=listing_title,
        members=members_resp,
        status=cast("ConversationStatus", conversation.status),
        unread_count=unread_count(conversation, actor_user_id),
    )


def unread_count(conversation: Conversation, actor_user_id: int) -> int:
    actor_member = next(
        (member for member in conversation.members if member.user_id == actor_user_id),
        None,
    )
    last_read_message_id = actor_member.last_read_message_id if actor_member else None
    return sum(
        1
        for message in conversation.messages
        if message.sender_user_id != actor_user_id
        and (last_read_message_id is None or message.id > last_read_message_id)
    )


def message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        attachments=[
            MessageAttachmentResponse(
                attachment_type=cast("AttachmentType", attachment.attachment_type),
                id=attachment.public_id,
                media_id=attachment.media_asset.public_id,
                metadata=attachment.metadata_json,
                public_url=attachment.media_asset.public_url
                if attachment.media_asset.status == "approved"
                else None,
                sort_order=attachment.sort_order,
            )
            for attachment in sorted(message.attachments, key=lambda item: item.sort_order)
        ],
        body=message.body,
        client_message_id=message.client_message_id,
        conversation_id=message.conversation.public_id,
        created_at=message.created_at,
        id=message.public_id,
        listing_id=message.listing.public_id if message.listing else None,
        message_type=cast("MessageType", message.message_type),
        metadata=message.metadata_json,
        read_by_user_ids=[read.user.public_id for read in message.reads],
        sender=UserSummary(id=message.sender.public_id),
    )


def message_report_response(report: MessageReport, message_public_id: str) -> MessageReportResponse:
    return MessageReportResponse(
        created_at=report.created_at,
        id=report.public_id,
        message_id=message_public_id,
        reason=report.reason,
        status=report.status,
    )
