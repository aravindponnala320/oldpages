from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BodyLimitMiddleware:
    """Refuses request bodies over max_bytes, with or without a Content-Length header.

    The API only takes JSON; photos go straight to object storage via presigned URLs.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            await self.too_large(scope, receive, send)
            return

        received = 0
        too_big = False
        started = False

        async def counted_receive() -> Message:
            nonlocal received, too_big
            if too_big:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    # Stop reading; whatever the app answers is replaced with a 413 below.
                    too_big = True
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal started
            if too_big:
                return
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, counted_receive, guarded_send)
        except Exception:
            if not too_big:
                raise
        if too_big and not started:
            await self.too_large(scope, receive, send)

    async def too_large(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            {
                "type": "https://oldpages.in/problems/request-too-large",
                "title": "Request Too Large",
                "status": 413,
                "detail": f"Request bodies are limited to {self.max_bytes // 1024} KB.",
            },
            status_code=413,
            media_type="application/problem+json",
        )
        await response(scope, receive, send)
