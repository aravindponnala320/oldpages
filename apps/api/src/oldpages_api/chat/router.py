from __future__ import annotations

import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.chat.schemas import (
    ChatRequestActionRequest,
    ChatRequestCreateRequest,
    ChatRequestResponse,
    ConversationListResponse,
    MessageCreateRequest,
    MessageListResponse,
    MessageReportRequest,
    MessageReportResponse,
    MessageResponse,
)
from oldpages_api.chat.service import ChatService
from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from oldpages_api.identity.exceptions import InvalidTokenError
from oldpages_api.identity.models import User
from oldpages_api.identity.service import IdentityService
from oldpages_api.shared.db.database import get_session

chat_requests_router = APIRouter(prefix="/chat-requests", tags=["chat requests"])
conversations_router = APIRouter(prefix="/conversations", tags=["conversations"])
websocket_router = APIRouter(tags=["websocket"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def chat_service(session: AsyncSession) -> ChatService:
    return ChatService(session)


@chat_requests_router.get("", response_model=list[ChatRequestResponse])
async def list_chat_requests(
    principal: PrincipalDep,
    session: SessionDep,
    role: str = Query(default="recipient"),
    chat_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[ChatRequestResponse]:
    return await chat_service(session).list_chat_requests(
        principal.user, role=role, status=chat_status, limit=limit
    )


@chat_requests_router.post(
    "",
    response_model=ChatRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_request(
    payload: ChatRequestCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ChatRequestResponse:
    return await chat_service(session).create_chat_request(
        payload,
        principal.user,
        request_context(request),
    )


@chat_requests_router.post("/{request_id}/accept", response_model=ChatRequestResponse)
async def accept_chat_request(
    request_id: str,
    payload: ChatRequestActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ChatRequestResponse:
    return await chat_service(session).accept_chat_request(
        request_id,
        payload,
        principal.user,
        request_context(request),
    )


@chat_requests_router.post("/{request_id}/decline", response_model=ChatRequestResponse)
async def decline_chat_request(
    request_id: str,
    payload: ChatRequestActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ChatRequestResponse:
    return await chat_service(session).decline_chat_request(
        request_id,
        payload,
        principal.user,
        request_context(request),
    )


@chat_requests_router.post("/{request_id}/block", response_model=ChatRequestResponse)
async def block_chat_request(
    request_id: str,
    payload: ChatRequestActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ChatRequestResponse:
    return await chat_service(session).block_chat_request(
        request_id,
        payload,
        principal.user,
        request_context(request),
    )


@conversations_router.get("", response_model=ConversationListResponse)
async def list_conversations(
    principal: PrincipalDep,
    session: SessionDep,
    cursor: str | None = Query(default=None, max_length=26),
    limit: int = Query(default=20, ge=1, le=50),
    listing_id: str | None = Query(default=None, max_length=26),
) -> ConversationListResponse:
    return await chat_service(session).list_conversations(
        principal.user,
        cursor=cursor,
        limit=limit,
        listing_id=listing_id,
    )


@conversations_router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def list_messages(
    conversation_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
    cursor: str | None = Query(default=None, max_length=26),
    limit: int = Query(default=50, ge=1, le=100),
) -> MessageListResponse:
    return await chat_service(session).list_messages(
        conversation_id,
        principal.user,
        cursor=cursor,
        limit=limit,
        context=request_context(request),
    )


@conversations_router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> MessageResponse:
    return await chat_service(session).send_message(
        conversation_id,
        payload,
        principal.user,
        request_context(request),
    )


@conversations_router.post(
    "/messages/{message_id}/report",
    response_model=MessageReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def report_message(
    message_id: str,
    payload: MessageReportRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> MessageReportResponse:
    return await chat_service(session).report_message(
        message_id,
        payload,
        principal.user,
        request_context(request),
    )


@websocket_router.websocket("/ws/conversations")
async def conversations_websocket(
    websocket: WebSocket,
    session: SessionDep,
    last_message_id: str | None = Query(default=None, max_length=26),
) -> None:
    actor = await authenticate_websocket(websocket, session)
    if actor is None:
        return
    await websocket.accept()

    service = chat_service(session)

    # Send missed messages (replay since last seen)
    replay = await service.websocket_replay(actor, last_message_id)
    await websocket.send_json({"type": "connected", "user_id": actor.public_id})
    for message in replay:
        await websocket.send_json({"type": "message.created", "message": message.model_dump(mode="json")})

    # Get all conversation IDs this user participates in
    conv_list = await service.list_conversations(actor)
    conv_ids = [c.id for c in conv_list.items]

    from oldpages_api.shared.cache.redis import get_redis
    redis = get_redis()
    pubsub = redis.pubsub()

    # Subscribe to conversation channels + user's personal channel
    channels = [f"user:{actor.public_id}"]
    if conv_ids:
        channels.extend([f"conversation:{cid}" for cid in conv_ids])
    await pubsub.subscribe(*channels)

    async def redis_listener() -> None:
        async for redis_msg in pubsub.listen():
            if redis_msg["type"] != "message":
                continue
            try:
                data = json.loads(redis_msg["data"])
                await websocket.send_json(data)
            except Exception:
                break

    async def ws_receiver() -> None:
        while True:
            try:
                payload = await websocket.receive_json()
                event_type = payload.get("type")
                if event_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif event_type == "close":
                    return
            except Exception:
                return

    try:
        await asyncio.gather(redis_listener(), ws_receiver())
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe()
        await pubsub.aclose()


async def authenticate_websocket(websocket: WebSocket, session: AsyncSession) -> User | None:
    token = websocket.query_params.get("access_token")
    authorization = websocket.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", maxsplit=1)[1]
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    try:
        user, _session_public_id = await IdentityService(
            session,
            websocket.app.state.settings,
        ).get_user_from_access_token(token)
    except InvalidTokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    return user
