import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.logger import logger


class RequestLogMiddleware(BaseHTTPMiddleware):
    """输出单行请求访问日志，不记录请求体和敏感头。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            process_time = (time.perf_counter() - start_time) * 1000
            client_host = request.client.host if request.client else "-"
            logger.info(
                "%s %s | status=%s | duration=%.2fms | client=%s",
                request.method,
                request.url.path,
                status_code,
                process_time,
                client_host,
            )
