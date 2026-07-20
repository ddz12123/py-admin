from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """应用存活检查响应。"""

    status: Literal["ok"] = Field(..., description="服务状态")


class ReadinessResponse(BaseModel):
    """应用就绪检查响应。"""

    status: Literal["ok"] = Field(..., description="服务状态")
    database: Literal["ok"] = Field(..., description="数据库状态")
