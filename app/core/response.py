from enum import IntEnum
from typing import Any

from fastapi.encoders import jsonable_encoder

SUCCESS_CODE = 0


class ErrorCode(IntEnum):
    """稳定的业务错误码；HTTP 状态码与业务码相互独立。"""

    BAD_REQUEST = 40000
    VALIDATION_ERROR = 42200
    AUTH_REQUIRED = 40100
    TOKEN_INVALID = 40101
    INVALID_CREDENTIALS = 40102
    FORBIDDEN = 40300
    ACCOUNT_DISABLED = 40301
    NOT_FOUND = 40400
    METHOD_NOT_ALLOWED = 40500
    CONFLICT = 40900
    USERNAME_EXISTS = 40901
    INTERNAL_ERROR = 50000
    SERVICE_UNAVAILABLE = 50300
    DATABASE_UNAVAILABLE = 50301


def success(data: Any = None, message: str = "success") -> dict[str, Any]:
    """成功响应；无返回数据时显式输出 data: null。"""
    return {"code": SUCCESS_CODE, "message": message, "data": jsonable_encoder(data)}


def fail(
    message: str = "error",
    data: Any = None,
    code: int | ErrorCode = ErrorCode.BAD_REQUEST,
) -> dict[str, Any]:
    """失败响应内容，HTTP 状态码由异常处理器或调用方决定。"""
    return {"code": int(code), "message": message, "data": jsonable_encoder(data)}
