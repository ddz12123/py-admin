from typing import Any

from fastapi.encoders import jsonable_encoder

# 业务状态码
SUCCESS_CODE = 0   # 成功
FAIL_CODE = 1      # 失败


def success(data: Any = None, message: str = "success") -> dict[str, Any]:
    """成功响应（HTTP 200 + 业务状态码 0）"""
    return {
        "code": SUCCESS_CODE,
        "message": message,
        "data": jsonable_encoder(data),
    }


def fail(message: str = "error", data: Any = None) -> dict[str, Any]:
    """失败响应内容（HTTP 状态码由调用方决定）"""
    return {
        "code": FAIL_CODE,
        "message": message,
        "data": jsonable_encoder(data),
    }
