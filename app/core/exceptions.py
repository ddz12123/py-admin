from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import logger
from app.core.response import ErrorCode, fail


class AppException(Exception):
    """可同时表达 HTTP 状态和稳定业务错误码的应用异常。"""

    def __init__(
        self,
        message: str = "应用错误",
        *,
        code: int | ErrorCode = ErrorCode.BAD_REQUEST,
        http_status: int = 400,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message
        self.http_status = http_status
        self.code = int(
            ErrorCode.INTERNAL_ERROR
            if http_status >= 500 and code == ErrorCode.BAD_REQUEST
            else code
        )
        self.data = data
        self.headers = headers
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message=message, code=ErrorCode.NOT_FOUND, http_status=404)


class ConflictException(AppException):
    def __init__(
        self,
        message: str = "资源冲突",
        *,
        code: int | ErrorCode = ErrorCode.CONFLICT,
    ):
        super().__init__(message=message, code=code, http_status=409)


class ServiceUnavailableException(AppException):
    def __init__(
        self,
        message: str = "服务暂不可用",
        *,
        code: int | ErrorCode = ErrorCode.SERVICE_UNAVAILABLE,
        data: Any = None,
    ):
        super().__init__(message=message, code=code, http_status=503, data=data)


def _format_validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        message = error.get("msg", "参数错误")
        if message.startswith("Value error, "):
            message = message[len("Value error, ") :]
        errors.append(
            {
                "field": ".".join(str(item) for item in error.get("loc", [])),
                "message": message,
                "type": error.get("type"),
            }
        )
    return errors


def _http_error_code(status_code: int) -> ErrorCode:
    return {
        401: ErrorCode.AUTH_REQUIRED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
        409: ErrorCode.CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }.get(status_code, ErrorCode.INTERNAL_ERROR if status_code >= 500 else ErrorCode.BAD_REQUEST)


def _http_error_message(status_code: int) -> str:
    return {
        400: "请求错误",
        401: "未认证或认证已失效",
        403: "权限不足",
        404: "请求的资源不存在",
        405: "请求方法不允许",
        409: "资源冲突",
        422: "请求参数校验失败",
        503: "服务暂不可用",
    }.get(status_code, "服务器内部错误" if status_code >= 500 else "请求失败")


def register_exception_handlers(app: FastAPI) -> None:
    """注册统一异常处理器，保证框架异常也遵循统一响应格式。"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = _format_validation_errors(exc)
        logger.warning(
            "[%s] %s %s - validation failed | request_id=%s",
            ErrorCode.VALIDATION_ERROR,
            request.method,
            request.url.path,
            getattr(request.state, "request_id", "-"),
        )
        return JSONResponse(
            status_code=422,
            content=fail(
                code=ErrorCode.VALIDATION_ERROR,
                message="请求参数校验失败",
                data={"errors": errors},
            ),
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "[%s] %s %s - %s | request_id=%s",
            exc.code,
            request.method,
            request.url.path,
            exc.message,
            getattr(request.state, "request_id", "-"),
        )
        data = None if exc.http_status >= 500 else exc.data
        message = _http_error_message(exc.http_status) if exc.http_status >= 500 else exc.message
        return JSONResponse(
            status_code=exc.http_status,
            content=fail(code=exc.code, message=message, data=data),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _http_error_code(exc.status_code)
        # 5xx 的 detail 可能包含数据库地址、凭据或内部实现信息，不直接返回给客户端。
        if exc.status_code >= 500:
            message = _http_error_message(exc.status_code)
            data = None
        elif isinstance(exc.detail, str):
            message = exc.detail
            data = None
        else:
            message = _http_error_message(exc.status_code)
            data = exc.detail
        logger.warning(
            "[%s] %s %s - %s | request_id=%s",
            code,
            request.method,
            request.url.path,
            message,
            getattr(request.state, "request_id", "-"),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(code=code, message=message, data=data),
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "[%s] %s %s - %s | request_id=%s",
            ErrorCode.INTERNAL_ERROR,
            request.method,
            request.url.path,
            exc,
            getattr(request.state, "request_id", "-"),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=fail(code=ErrorCode.INTERNAL_ERROR, message="服务器内部错误"),
        )
