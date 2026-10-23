import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logger import logger


class RequestLogMiddleware:
    """输出单行请求访问日志，不记录请求体和敏感头。"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        status_code = 500
        request_id = scope.get("state", {}).get("request_id", "-")
        method = scope.get("method", "-")
        path = scope.get("path", "-")
        client = scope.get("client")
        client_host = client[0] if client else "-"

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.info(
                "%s %s | status=%s | duration=%.2fms | client=%s | request_id=%s",
                method,
                path,
                status_code,
                process_time,
                client_host,
                request_id,
            )
