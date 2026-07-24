from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    """统一的环境变量读取规则。"""

    model_config = SettingsConfigDict(
        env_prefix="PY_ADMIN_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
    )


class AppSettings(EnvSettings):
    """应用运行配置。"""

    PROJECT_NAME: str = "Py-Admin"
    PROJECT_VERSION: str = "0.1.0"
    DESCRIPTION: str = "FastAPI Admin Backend"
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, ge=1, le=65535)
    RELOAD: bool = False

    @model_validator(mode="after")
    def validate_environment(self) -> "AppSettings":
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("生产环境不能开启 DEBUG")
            if self.RELOAD:
                raise ValueError("生产环境不能开启 RELOAD")
        return self


class LoggingSettings(EnvSettings):
    """日志配置。"""

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    ACCESS_LOG_ENABLED: bool = True

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


class DatabaseSettings(EnvSettings):
    """数据库配置，可供 Alembic 独立加载。"""

    DATABASE_URL: str = ""
    SQL_ECHO: bool = False
    DB_POOL_SIZE: int = Field(default=10, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0)
    DB_POOL_RECYCLE: int = Field(default=3600, ge=0)

    @model_validator(mode="after")
    def validate_database_url(self) -> "DatabaseSettings":
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL 未配置，请在 .env 文件中设置")
        return self


class CorsSettings(EnvSettings):
    """跨域配置。"""

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = False

    @field_validator("CORS_ORIGINS")
    @classmethod
    def normalize_cors_origins(cls, origins: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(origin.strip() for origin in origins if origin.strip()))
        if not normalized:
            raise ValueError("CORS_ORIGINS 不能为空")
        return normalized

    @model_validator(mode="after")
    def validate_credentials(self) -> "CorsSettings":
        if self.CORS_ALLOW_CREDENTIALS and "*" in self.CORS_ORIGINS:
            raise ValueError("CORS 允许携带凭证时，CORS_ORIGINS 不能使用通配符 *")
        return self


class DocsSettings(EnvSettings):
    """OpenAPI 与 Swagger UI 配置；生产环境由应用强制关闭。"""

    DOCS_ENABLED: bool = True
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    SWAGGER_JS_URL: str = (
        "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js"
    )
    SWAGGER_CSS_URL: str = (
        "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui.css"
    )

    @field_validator("DOCS_URL", "REDOC_URL", "OPENAPI_URL")
    @classmethod
    def validate_route_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("文档路径必须以 / 开头")
        return value


class Settings(BaseModel):
    """按领域聚合全部应用配置。"""

    app: AppSettings = Field(default_factory=AppSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)
    docs: DocsSettings = Field(default_factory=DocsSettings)

    @model_validator(mode="after")
    def validate_cross_domain_config(self) -> "Settings":
        if self.app.ENVIRONMENT == "production" and "*" in self.cors.CORS_ORIGINS:
            raise ValueError("生产环境必须显式配置 CORS_ORIGINS")
        return self


@lru_cache
def get_settings() -> Settings:
    """获取进程级配置，适用于启动脚本等非请求场景。"""
    return Settings()


def get_database_url() -> str:
    """获取数据库连接地址，Alembic 只加载数据库领域配置。"""
    return DatabaseSettings().DATABASE_URL
