from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logger import logger
from app.core.response import ErrorCode, fail


class GlobalExceptionMiddleware:
    """在 CORS 中间件内侧兜底未处理异常，保证 500 响应也带上 CORS 头。

    Starlette 把 @app.exception_handler(Exception) 注册在整个中间件栈最外层，
    其产生的 500 响应不会经过 CORSMiddleware，浏览器会报跨域错误而拿不到响应体。
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            request = Request(scope)
            logger.error(
                "[%s] %s %s - %s | request_id=%s",
                ErrorCode.INTERNAL_ERROR,
                request.method,
                request.url.path,
                exc,
                scope.get("state", {}).get("request_id", "-"),
                exc_info=True,
            )
            if response_started:
                raise
            response = JSONResponse(
                status_code=500,
                content=fail(code=ErrorCode.INTERNAL_ERROR, message="服务器内部错误"),
            )
            await response(scope, receive, send)
