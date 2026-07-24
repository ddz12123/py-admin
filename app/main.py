from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings
from app.core.exceptions import register_exception_handlers
from app.core.logger import logger, setup_logging
from app.db.session import create_db_engine, create_session_factory
from app.middlewares.request_log_middleware import RequestLogMiddleware


def create_lifespan(settings: Settings):
    """为指定配置创建应用生命周期。"""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings.database)
        app.state.db_engine = engine
        app.state.db_session_factory = create_session_factory(engine)
        logger.info("应用启动：environment=%s", settings.app.ENVIRONMENT)
        try:
            yield
        finally:
            await engine.dispose()
            logger.info("应用关闭：数据库连接池已释放")

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """创建相互独立、可注入配置的 FastAPI 应用实例。"""
    app_settings = settings if settings is not None else Settings()
    setup_logging(
        app_settings.logging.LOG_LEVEL,
        disable_uvicorn_access_log=app_settings.logging.ACCESS_LOG_ENABLED,
    )

    docs_enabled = (
        app_settings.docs.DOCS_ENABLED
        and app_settings.app.ENVIRONMENT != "production"
    )
    app = FastAPI(
        title=app_settings.app.PROJECT_NAME,
        version=app_settings.app.PROJECT_VERSION,
        description=app_settings.app.DESCRIPTION,
        debug=app_settings.app.DEBUG,
        lifespan=create_lifespan(app_settings),
        docs_url=app_settings.docs.DOCS_URL if docs_enabled else None,
        redoc_url=app_settings.docs.REDOC_URL if docs_enabled else None,
        openapi_url=app_settings.docs.OPENAPI_URL if docs_enabled else None,
        swagger_js_url=app_settings.docs.SWAGGER_JS_URL,
        swagger_css_url=app_settings.docs.SWAGGER_CSS_URL,
    )
    app.state.settings = app_settings

    if app_settings.logging.ACCESS_LOG_ENABLED:
        app.add_middleware(RequestLogMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors.CORS_ORIGINS,
        allow_credentials=app_settings.cors.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)
    return app
