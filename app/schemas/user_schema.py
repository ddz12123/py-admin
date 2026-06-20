from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class UserResponse(BaseModel):
    """用户响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    status: int = Field(..., description="状态: 0=禁用, 1=可用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    @field_serializer("created_at", "updated_at")
    @classmethod
    def serialize_datetime(cls, v: datetime) -> str:
        return v.strftime("%Y-%m-%d %H:%M:%S")


class UserListRequest(BaseModel):
    """用户列表查询参数"""
    page: int = Field(..., ge=1, description="页码")
    page_size: int = Field(..., ge=1, le=100, description="每页数量")
    username: str | None = Field(None, description="用户名模糊查询")


class UserListResponse(BaseModel):
    """用户列表响应"""
    items: list[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
