import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# 按项目根目录定位 .env，避免从其他工作目录启动时读不到配置。
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class EnvSettings(BaseSettings):
    """统一的环境变量读取规则。"""

    model_config = SettingsConfigDict(
        env_prefix="PY_ADMIN_",
        env_file=ENV_FILE,
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
    """数据库配置，可供应用和 Alembic 独立加载。"""

    DATABASE_URL: str = ""
    SQL_ECHO: bool = False
    DB_POOL_SIZE: int = Field(default=10, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0)
    DB_POOL_TIMEOUT: float = Field(default=30.0, gt=0)
    DB_POOL_RECYCLE: int = Field(default=3600, ge=0)
    DB_HEALTHCHECK_TIMEOUT: float = Field(default=2.0, gt=0, le=30.0)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_database_url(self) -> "DatabaseSettings":
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL 未配置，请在 .env 文件中设置")
        return self


class CorsSettings(EnvSettings):
    """跨域配置。"""

    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        # 环境变量同时支持 JSON 数组和逗号分隔两种写法。
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                try:
                    return json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError("CORS_ORIGINS 必须是合法 JSON 数组或逗号分隔字符串") from exc
            return text.split(",")
        return value

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
    """OpenAPI、Swagger UI 配置；生产环境由应用强制关闭。"""

    # 文档地址需要支持“显式留空”来关闭对应页面。
    model_config = SettingsConfigDict(**{**EnvSettings.model_config, "env_ignore_empty": False})

    DOCS_ENABLED: bool = True
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    SWAGGER_JS_URL: str = (
        "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js"
    )
    SWAGGER_CSS_URL: str = "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui.css"

    @field_validator("DOCS_URL", "OPENAPI_URL")
    @classmethod
    def validate_route_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("文档路径必须以 / 开头")
        return value

    @field_validator("REDOC_URL")
    @classmethod
    def validate_redoc_path(cls, value: str) -> str:
        # ReDoc 留空可单独禁用，非空时必须是绝对路由路径。
        if value and not value.startswith("/"):
            raise ValueError("文档路径必须以 / 开头")
        return value

    @model_validator(mode="after")
    def validate_route_uniqueness(self) -> "DocsSettings":
        paths = [path for path in (self.DOCS_URL, self.REDOC_URL, self.OPENAPI_URL) if path]
        if len(paths) != len(set(paths)):
            raise ValueError("DOCS_URL、REDOC_URL 和 OPENAPI_URL 不能重复")
        return self


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
