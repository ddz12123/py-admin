# Py-Admin

一个不绑定具体业务的 FastAPI 后端基础模板，提供应用工厂、领域化配置、异步数据库会话、请求级事务、Alembic、统一响应与异常、OpenAPI 错误模型、访问日志和健康检查。

模板本身不包含用户、登录、权限、菜单、部门等业务模块。如何新增模块请阅读 [模块开发指南](docs/module-development-guide.md)。

## 技术栈

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0（异步）
- MySQL / aiomysql
- Alembic
- Pydantic Settings
- uv

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，至少修改数据库地址：

```powershell
Copy-Item .env.example .env
```

### 3. 创建数据库并执行迁移

```sql
CREATE DATABASE py_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
uv run alembic upgrade head
```

当前模板没有业务表，因此首次使用时可以直接创建自己的模型和迁移。

### 4. 启动服务

```bash
uv run main.py
```

开发环境默认地址：

- 健康检查：`http://127.0.0.1:8000/api/system/health`
- 就绪检查：`http://127.0.0.1:8000/api/system/health/ready`
- Swagger：`http://127.0.0.1:8000/docs`

## 配置结构

内部配置按领域拆分：

- `settings.app`：应用名称、环境、监听地址
- `settings.logging`：日志
- `settings.database`：数据库和连接池
- `settings.cors`：跨域
- `settings.docs`：OpenAPI、Swagger 和 ReDoc

外部环境变量继续使用扁平的 `PY_ADMIN_` 前缀，便于容器和部署平台注入。

生产环境约束：

- 禁止 `DEBUG=true`
- 禁止 `RELOAD=true`
- 必须显式配置 CORS 来源
- 强制关闭 Swagger、ReDoc 和 OpenAPI，不受 `DOCS_ENABLED` 影响

Swagger 静态资源地址已经配置化，默认保持当前 BootCDN：

```env
PY_ADMIN_SWAGGER_JS_URL=https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js
PY_ADMIN_SWAGGER_CSS_URL=https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui.css
```

## 数据库约定

- 所有模型继承 `app.db.base.Base`
- 需要创建、更新时间的模型同时继承 `TimestampMixin`
- 约束、索引和外键使用统一命名规范，保证 Alembic 迁移名称稳定
- 应用时间统一使用带时区的 UTC `datetime`
- API 时间交给 Pydantic 输出 ISO 8601，不手写 `strftime`
- 应用启动时不自动建表，数据库结构统一由 Alembic 管理

## Session 与事务

- `get_db`：查询场景，只管理 Session 生命周期
- `get_transactional_db`：写入场景，请求成功自动提交，异常自动回滚
- Service 不自行调用 `commit()` 或 `rollback()`
- 需要提前检查约束或获取数据库结果时使用 `flush()`

## 统一响应与错误

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

错误响应：

```json
{
  "code": 40000,
  "message": "请求错误",
  "data": null
}
```

`app.core.openapi.error_responses()` 用于把错误响应同步声明到 OpenAPI。框架只保留通用错误码，具体模块在模块内部定义自己的错误码。

## 健康检查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/system/health` | 存活检查兼容路径 |
| GET | `/api/system/health/live` | 存活检查 |
| GET | `/api/system/health/ready` | 验证数据库连接 |
