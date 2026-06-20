from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""

    code: int = 0
    message: str = "success"
    data: T | None = None


class EmptyResponse(BaseModel):
    """空响应数据"""

    pass
