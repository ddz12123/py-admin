# Py-Admin

基于 FastAPI 的后台管理框架

## 技术栈

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 (异步)
- MySQL
- Alembic (数据库迁移)
- JWT 认证

## 项目结构

```
py-admin/
├── app/
│   ├── main.py                 # 应用入口
│   ├── api/
│   │   ├── router.py           # 路由聚合
│   │   └── routes/             # 路由层
│   ├── core/                   # 核心模块
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # JWT、密码加密
│   │   ├── response.py         # 统一响应
│   │   ├── exceptions.py       # 异常处理
│   │   └── logger.py           # 日志
│   ├── db/                     # 数据库
│   │   ├── base.py             # ORM 基类
│   │   └── session.py          # 异步 Session
│   ├── dependencies/           # 依赖注入
│   ├── middlewares/            # 中间件
│   │   ├── auth_middleware.py   # JWT 鉴权
│   │   └── request_log_middleware.py  # 请求日志
│   ├── models/                 # 数据模型
│   ├── schemas/                # 请求/响应模型
│   └── services/               # 业务逻辑
├── alembic/                    # 数据库迁移
├── main.py                     # 启动入口
├── pyproject.toml
├── .env                        # 环境变量
└── .env.example
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，修改数据库配置：

```bash
cp .env.example .env
```

`.env` 配置项：

```env
# 项目配置
PY_ADMIN_PROJECT_NAME=Py-Admin
PY_ADMIN_PROJECT_VERSION=0.1.0
PY_ADMIN_DEBUG=true

# 数据库
PY_ADMIN_DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/py_admin?charset=utf8mb4

# JWT
PY_ADMIN_SECRET_KEY=your-secret-key-here
PY_ADMIN_ALGORITHM=HS256
PY_ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
PY_ADMIN_CORS_ORIGINS=["*"]
PY_ADMIN_CORS_ALLOW_CREDENTIALS=false
```

### 3. 创建数据库

```sql
CREATE DATABASE py_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 执行数据库迁移

```bash
uv run alembic upgrade head
```

### 5. 启动服务

```bash
uv run main.py
```

访问 API 文档：http://127.0.0.1:8000/docs

## API 接口

### 认证接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/auth/register | 用户注册 | 否 |
| POST | /api/auth/login | 用户登录 | 否 |

### 用户接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/users/me | 获取当前用户信息 | 是 |
| GET | /api/users | 获取用户列表 | 是 |

### 系统接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/system/health | 健康检查 | 否 |

## 响应格式

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 失败响应

```json
{
  "code": 1,
  "message": "错误信息",
  "data": null
}
```

## 认证方式

在 Swagger UI 右上角点击 **Authorize** 按钮，输入 JWT Token（不需要 Bearer 前缀）。

或在请求头添加：

```
Authorization: Bearer <token>
```

## 数据库迁移 (Alembic)

应用启动时不会自动建表，数据库结构统一由 Alembic 管理。

### 常用命令

```bash
# 自动生成迁移（对比 model 和数据库差异）
uv run alembic revision --autogenerate -m "描述信息"

# 执行所有迁移
uv run alembic upgrade head

# 回滚最近一次迁移
uv run alembic downgrade -1

# 回滚到指定版本
uv run alembic downgrade <revision_id>

# 查看当前版本
uv run alembic current

# 查看迁移历史
uv run alembic history

# 查看迁移历史（详细）
uv run alembic history --verbose
```

### 工作流程

1. 修改 `app/models/` 下的模型文件
2. 生成迁移：`uv run alembic revision --autogenerate -m "描述"`
3. 检查 `alembic/versions/` 下生成的迁移文件
4. 执行迁移：`uv run alembic upgrade head`

### 示例

```bash
# 用户表添加 status 字段
# 1. 修改 app/models/user.py 添加字段
# 2. 生成迁移
uv run alembic revision --autogenerate -m "add status to users"
# 3. 执行迁移
uv run alembic upgrade head
```

### 注意事项

- 迁移文件会自动检测 model 变化，但复杂变更（如重命名）需手动修改
- 生产环境执行迁移前建议先备份数据库
- `render_as_batch=True` 已配置，支持 MySQL 的 ALTER TABLE 操作

## 开发规范

- 业务状态码：0=成功，1=失败
- HTTP 状态码：200=成功，400=业务错误，401=未登录/登录过期/Token 无效，403=权限不足，404=资源不存在，500=服务器内部错误
- 密码使用 bcrypt 加密
- JWT Token 有效期默认 30 分钟
- 配置项优先使用 `PY_ADMIN_` 前缀，避免被系统同名环境变量污染
- 路由层只做参数接收和响应组织，业务逻辑放在 `services/`
- 返回结构统一为 `{code, message, data}`，接口文档通过 `ResponseModel[T]` 描述 `data` 类型
