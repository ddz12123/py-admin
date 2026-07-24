from enum import IntEnum
from typing import Any

from fastapi.encoders import jsonable_encoder

SUCCESS_CODE = 0


class ErrorCode(IntEnum):
    """框架级稳定错误码；模块应在自己的命名空间中扩展业务错误码。"""

    BAD_REQUEST = 40000
    VALIDATION_ERROR = 42200
    AUTH_REQUIRED = 40100
    FORBIDDEN = 40300
    NOT_FOUND = 40400
    METHOD_NOT_ALLOWED = 40500
    CONFLICT = 40900
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
