# Py-Admin

一个面向通用后台项目的 FastAPI 基础框架模板，提供应用工厂、异步数据库会话、声明式 JWT 认证、统一响应与异常、配置校验、访问日志和健康检查等基础能力。

## 技术栈

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0（异步）
- MySQL / aiomysql
- Alembic
- Pydantic Settings
- JWT

## 项目结构

```text
py-admin/
├── app/
│   ├── main.py                 # create_app 应用工厂与 lifespan
│   ├── api/
│   │   ├── router.py           # 路由聚合
│   │   └── routes/             # 路由层
│   ├── core/
│   │   ├── config.py           # 配置读取与启动校验
│   │   ├── security.py         # JWT、密码哈希
│   │   ├── response.py         # 统一响应与业务错误码
│   │   ├── exceptions.py       # 统一异常处理
│   │   └── logger.py           # 日志配置
│   ├── db/
│   │   ├── base.py             # ORM Base
│   │   └── session.py          # Engine、Session 与事务依赖
│   ├── dependencies/
│   │   ├── auth.py             # Depends(get_current_user) 认证
│   │   └── config.py           # 当前应用配置依赖
│   ├── middlewares/
│   │   └── request_log_middleware.py
│   ├── models/
│   ├── schemas/
│   └── services/
├── alembic/
├── main.py                     # 本地启动入口
├── pyproject.toml
└── .env.example
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，至少修改数据库地址和 JWT 密钥：

```bash
cp .env.example .env
```

主要配置：

```env
# 应用
PY_ADMIN_ENVIRONMENT=development
PY_ADMIN_DEBUG=true
PY_ADMIN_HOST=0.0.0.0
PY_ADMIN_PORT=8000
PY_ADMIN_RELOAD=true

# 日志
PY_ADMIN_LOG_LEVEL=DEBUG
PY_ADMIN_ACCESS_LOG_ENABLED=true

# 数据库
PY_ADMIN_DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/py_admin?charset=utf8mb4
PY_ADMIN_SQL_ECHO=true
PY_ADMIN_DB_POOL_SIZE=10
PY_ADMIN_DB_MAX_OVERFLOW=20
PY_ADMIN_DB_POOL_RECYCLE=3600

# JWT
PY_ADMIN_SECRET_KEY=your-secret-key-change-in-production
PY_ADMIN_ALGORITHM=HS256
PY_ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
PY_ADMIN_CORS_ORIGINS=["*"]
PY_ADMIN_CORS_ALLOW_CREDENTIALS=false
```

配置约束：

- 所有应用配置统一使用 `PY_ADMIN_` 前缀。
- `production` 环境禁止开启 `DEBUG` 和 `RELOAD`。
- 生产环境必须显式配置 CORS 来源，并使用至少 32 位的非示例 JWT 密钥。
- `CORS_ALLOW_CREDENTIALS=true` 时不能同时配置通配符来源 `*`。
- Alembic 仅加载数据库配置，不依赖 JWT 等应用运行配置。

### 3. 创建数据库并执行迁移

```sql
CREATE DATABASE py_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
uv run alembic upgrade head
```

### 4. 启动服务

```bash
uv run main.py
```

也可以直接使用 Uvicorn 的应用工厂模式：

```bash
uv run uvicorn app.main:create_app --factory
```

访问 API 文档：`http://127.0.0.1:8000/docs`

## 应用工厂

`app.main` 不再创建模块级全局 `app`、Engine 或 SessionFactory。每次调用 `create_app()` 都会创建独立应用，数据库资源在 lifespan 启动阶段创建，在应用关闭时释放。

测试或不同部署环境可以直接注入配置：

```python
from app.core.config import Settings
from app.main import create_app

settings = Settings(
    DATABASE_URL="sqlite+aiosqlite:///./test.db",
    SECRET_KEY="test-secret",
    ENVIRONMENT="testing",
)
app = create_app(settings)
```

当前应用使用的配置和数据库资源分别保存在 `app.state.settings`、`app.state.db_engine` 和 `app.state.db_session_factory` 中，不依赖模块级可变全局对象。

## 声明式认证

认证不再通过全局 Middleware 拦截路径，而是在需要认证的接口上显式声明依赖：

```python
from fastapi import Depends

from app.dependencies.auth import get_current_user
from app.models.user import User


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

这样公开接口默认公开，受保护接口在代码和 OpenAPI 文档中都能直接看出认证要求，也不需要维护容易误匹配的公开路径白名单。

## Session 与事务边界

框架提供两个数据库依赖：

- `get_db`：只负责 Session 生命周期，不自动提交，适合查询接口。
- `get_transactional_db`：开启请求级事务，接口正常结束自动提交，出现异常自动回滚并关闭 Session，适合写接口。

写接口应使用 function scope，保证事务提交在响应发送前完成；如果提交失败，仍能进入统一异常处理：

```python
@router.post("/items")
async def create_item(
    req: ItemCreate,
    db: AsyncSession = Depends(get_transactional_db, scope="function"),
):
    return await item_service.create(db, req)
```

Service 只执行 `add()`、`flush()` 和查询，不在内部随意 `commit()` / `rollback()`。需要提前获得主键或捕获唯一约束时使用 `flush()`，最终事务结果由路由声明的事务依赖统一决定。

> 后台任务不要复用请求依赖提供的 Session，应在后台任务内部重新创建 Session。

## 统一响应与错误码

所有正常响应和框架异常统一使用：

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

`data` 可以是对象、数组或 `null`。HTTP 状态码表达协议语义，`code` 表达稳定的业务错误类型，两者不再混为一个固定的 `code=1`。

示例：

```json
{
  "code": 40901,
  "message": "用户名已存在",
  "data": null
}
```

内置错误码分段：

| 范围/示例 | 含义 |
|---|---|
| `0` | 成功 |
| `40000` | 通用请求或业务参数错误 |
| `40100-40199` | 认证错误 |
| `40300-40399` | 权限或账号状态错误 |
| `40400` | 资源不存在 |
| `40500` | 请求方法不允许 |
| `40900-40999` | 资源冲突 |
| `42200` | 请求模型校验错误 |
| `50000` | 未处理的内部错误 |
| `50300-50399` | 服务或基础设施暂不可用 |

业务模块可以继续在对应区间扩展稳定错误码。FastAPI/Starlette 的 404、405 等 HTTP 异常也会转换为统一响应格式。

## 日志

- 日志级别由 `PY_ADMIN_LOG_LEVEL` 配置。
- 日志初始化可以重复执行，不会重复添加 Handler。
- 自定义访问日志使用单行格式记录 method、path、status、duration 和 client，不记录请求体、Token 等敏感数据。
- 开启自定义访问日志时会关闭 Uvicorn 的重复访问日志。
- 当前未引入 Request ID；后续有链路追踪需求时再统一接入。

## 健康检查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/system/health` | 存活检查兼容路径，不访问外部依赖 |
| GET | `/api/system/health/live` | 存活检查，不访问外部依赖 |
| GET | `/api/system/health/ready` | 就绪检查，执行 `SELECT 1` 验证数据库 |

数据库不可用时，ready 接口返回 HTTP 503 和业务错误码 `50301`。

## API 接口

### 认证接口

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| POST | `/api/auth/register` | 用户注册 | 否 |
| POST | `/api/auth/login` | 用户登录 | 否 |

### 用户接口

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/api/users/me` | 获取当前用户信息 | 是 |
| GET | `/api/users` | 获取用户列表 | 是 |

在 Swagger UI 右上角点击 **Authorize**，输入 JWT Token（不需要手动输入 Bearer 前缀）；或发送请求头：

```http
Authorization: Bearer <token>
```

## 数据库迁移

应用启动时不会自动建表，数据库结构统一由 Alembic 管理。

```bash
# 自动生成迁移
uv run alembic revision --autogenerate -m "描述"

# 执行全部迁移
uv run alembic upgrade head

# 回滚最近一次迁移
uv run alembic downgrade -1

# 查看当前版本和历史
uv run alembic current
uv run alembic history --verbose
```

生产环境执行迁移前应先检查迁移文件并备份数据库。

## 开发约定

- 路由层负责参数接收、依赖声明和响应组织。
- Service 负责用例逻辑，但不自行决定请求级事务提交。
- 需要认证的接口显式声明 `Depends(get_current_user)`。
- 成功码固定为 `0`，失败使用可区分、可扩展的稳定业务错误码。
- 返回结构统一为 `{code, message, data}`，接口文档使用 `ResponseModel[T]` 描述 `data`。
- 本模板只提供通用基础设施，不预置 RBAC、Repository、DDD、多租户等具体业务架构。
