from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logger import logger
from app.core.response import FAIL_CODE


class AppException(Exception):
    """业务异常，默认返回 HTTP 400"""

    def __init__(self, message: str = "应用错误", http_status: int = 400):
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class AuthException(AppException):
    """认证异常，仅用于未登录、登录过期、Token 无效等场景"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message=message, http_status=401)


class PermissionException(AppException):
    """权限异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message=message, http_status=403)


class NotFoundException(AppException):
    """资源不存在异常"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(message=message, http_status=404)


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """请求参数验证异常"""
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            msg = first_error.get("msg", "参数错误")
            # 去掉 Pydantic 的 "Value error, " 前缀
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
            message = msg
        else:
            message = "请求参数错误"

        logger.warning(f"[422] {request.method} {request.url.path} - {message}")
        return JSONResponse(
            status_code=422,
            content={
                "code": FAIL_CODE,
                "message": message,
                "data": None,
            },
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(f"[{exc.http_status}] {request.method} {request.url.path} - {exc.message}")
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "code": FAIL_CODE,
                "message": exc.message,
                "data": None,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"[500] {request.method} {request.url.path} - {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": FAIL_CODE,
                "message": "服务器内部错误",
                "data": None,
            },
        )
