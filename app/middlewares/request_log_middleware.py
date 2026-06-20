import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.logger import logger


class RequestLogMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()

        # 请求信息
        logger.info(f"--> {request.method} {request.url.path}")

        response = await call_next(request)

        # 耗时
        process_time = (time.time() - start_time) * 1000
        logger.info(f"<-- {request.method} {request.url.path} | {response.status_code} | {process_time:.2f}ms")

        return response
