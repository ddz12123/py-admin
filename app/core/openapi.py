from typing import Any

from app.schemas.response_schema import ErrorResponse

ERROR_RESPONSE_DESCRIPTIONS = {
    400: "请求错误",
    401: "未认证或认证已失效",
    403: "权限不足",
    404: "资源不存在",
    405: "请求方法不允许",
    409: "资源冲突",
    422: "请求参数校验失败",
    500: "服务器内部错误",
    503: "服务暂不可用",
}


def error_responses(*status_codes: int) -> dict[int, dict[str, Any]]:
    """生成可复用的 OpenAPI 错误响应声明。"""
    return {
        status_code: {
            "model": ErrorResponse,
            "description": ERROR_RESPONSE_DESCRIPTIONS[status_code],
        }
        for status_code in status_codes
    }


COMMON_ERROR_RESPONSES = error_responses(400, 422, 500)
