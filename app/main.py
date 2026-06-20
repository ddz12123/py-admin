from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.db.session import engine
from app.middlewares.auth_middleware import AuthMiddleware, PUBLIC_PATHS
from app.middlewares.request_log_middleware import RequestLogMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    yield

    # 关闭时
    await engine.dispose()


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
        # 国内 CDN 源
        swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui.css",
    )

    # 添加 JWT 安全方案到 OpenAPI
    from fastapi.openapi.utils import get_openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=settings.PROJECT_NAME,
            version=settings.PROJECT_VERSION,
            description=settings.DESCRIPTION,
            routes=app.routes,
        )
        # 定义安全方案
        openapi_schema.setdefault("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "输入 JWT Token（不需要 Bearer 前缀）",
            }
        }
        # 只给受保护接口标记鉴权，避免注册/登录/健康检查文档误导调用方
        for path, methods in openapi_schema.get("paths", {}).items():
            if path in PUBLIC_PATHS:
                continue
            for method, detail in methods.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                detail["security"] = [{"BearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # 请求日志中间件
    app.add_middleware(RequestLogMiddleware)

    # JWT 认证中间件
    app.add_middleware(AuthMiddleware)

    # CORS 中间件最后添加，保证认证失败等提前返回也能带上跨域响应头
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册全局异常处理
    register_exception_handlers(app)

    # 注册路由
    app.include_router(api_router)

    return app


app = create_app()
