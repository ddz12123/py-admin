from re import fullmatch
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = b"x-request-id"
_REQUEST_ID_PATTERN = r"[A-Za-z0-9._-]{1,128}"


def _get_request_id(scope: Scope) -> str:
    for name, value in scope.get("headers", []):
        if name.lower() == REQUEST_ID_HEADER:
            request_id = value.decode("latin-1")
            if fullmatch(_REQUEST_ID_PATTERN, request_id):
                return request_id
    return uuid4().hex


class RequestIDMiddleware:
    """为每个 HTTP 请求生成或透传请求 ID，并回写到响应头。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _get_request_id(scope)
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                if not any(name.lower() == REQUEST_ID_HEADER for name, _ in headers):
                    headers.append((REQUEST_ID_HEADER, request_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
