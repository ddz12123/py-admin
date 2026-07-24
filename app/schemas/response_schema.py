from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一成功响应模型。"""

    code: int = 0
    message: str = "success"
    data: T | None = None


class ErrorResponse(BaseModel):
    """统一错误响应模型，用于运行时响应和 OpenAPI 文档。"""

    code: int = Field(..., description="稳定错误码")
    message: str = Field(..., description="错误信息")
    data: Any = Field(default=None, description="可选错误详情")
