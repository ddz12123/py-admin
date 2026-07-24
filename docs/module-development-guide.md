# 模块开发指南

本文说明如何在基础模板中增加业务模块。模板不预置用户、权限或其他具体业务，下面使用通用的 `Item` 作为结构示例，实际项目中请替换为自己的领域名称。

## 1. 推荐文件结构

```text
app/
├── api/routes/item_routes.py
├── models/item.py
├── schemas/item_schema.py
└── services/item_service.py
```

保持职责简单：

- Route：接收参数、声明依赖、组织响应
- Schema：请求和响应的数据结构
- Service：用例逻辑和数据库查询
- Model：数据库表映射
- Core：只放真正跨模块的基础设施，不放模块业务规则

## 2. 创建模型

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class Item(TimestampMixin, Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
```

时间约定：

- `TimestampMixin` 统一生成 UTC 创建时间和更新时间
- 不在 Schema 中使用 `strftime`
- Pydantic 默认输出 ISO 8601 时间
- 数据库、容器和操作系统建议统一使用 UTC 时区

然后在 `app/models/__init__.py` 中导入模型，Alembic 才能发现它：

```python
from app.models.item import Item

__all__ = ["Item"]
```

## 3. 创建 Schema

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
```

## 4. 编写 Service

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.schemas.item_schema import ItemCreateRequest


async def create_item(db: AsyncSession, req: ItemCreateRequest) -> Item:
    item = Item(name=req.name)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item
```

Service 不调用 `commit()` 或 `rollback()`，事务由路由使用的数据库依赖统一管理。

## 5. 定义模块错误码

不要把具体业务错误码添加到框架级 `ErrorCode`。模块可以在自己的 Service 或独立模块目录中定义：

```python
from enum import IntEnum


class ItemErrorCode(IntEnum):
    ITEM_NOT_FOUND = 40410
    ITEM_NAME_EXISTS = 40910
```

抛出异常时继续使用框架异常：

```python
from app.core.exceptions import ConflictException

raise ConflictException(
    message="名称已存在",
    code=ItemErrorCode.ITEM_NAME_EXISTS,
)
```

## 6. 创建路由并声明 OpenAPI 错误响应

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.openapi import error_responses
from app.core.response import success
from app.db.session import get_transactional_db
from app.schemas.item_schema import ItemCreateRequest, ItemResponse
from app.schemas.response_schema import ResponseModel
from app.services import item_service

router = APIRouter(prefix="/items", tags=["项目"])


@router.post(
    "",
    response_model=ResponseModel[ItemResponse],
    responses=error_responses(409),
)
async def create_item(
    req: ItemCreateRequest,
    db: AsyncSession = Depends(get_transactional_db, scope="function"),
):
    item = await item_service.create_item(db, req)
    return success(data=ItemResponse.model_validate(item))
```

顶层 `api_router` 已统一声明 400、422、500 错误模型；接口额外可能出现的 401、403、404、409、503 等状态，应使用 `error_responses()` 显式补充。

## 7. 注册路由

修改 `app/api/router.py`：

```python
from app.api.routes import item_routes

api_router.include_router(item_routes.router)
```

当前模板固定使用 `/api` 前缀，不增加 API 版本号。

## 8. 生成迁移

```bash
uv run alembic revision --autogenerate -m "create items table"
uv run alembic upgrade head
```

提交迁移前检查：

- 表和字段是否正确
- 唯一约束、外键和索引是否存在
- `upgrade` 和 `downgrade` 是否成对
- 是否意外删除了其他表或字段

## 9. 配置读取

请求中通过依赖获取聚合配置：

```python
from fastapi import Depends

from app.core.config import Settings
from app.dependencies.config import get_app_settings


async def endpoint(settings: Settings = Depends(get_app_settings)):
    environment = settings.app.ENVIRONMENT
    database_url = settings.database.DATABASE_URL
```

新增基础设施配置时创建独立的配置类，再挂到 `Settings`；不要把业务数据或数据库中的动态规则放进环境配置。
