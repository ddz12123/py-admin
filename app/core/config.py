from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """仅包含数据库配置，供 Alembic 等独立命令使用。"""

    DATABASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_prefix="PY_ADMIN_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
    )


class Settings(DatabaseSettings):
    """应用运行配置。"""

    PROJECT_NAME: str = "Py-Admin"
    PROJECT_VERSION: str = "0.1.0"
    DESCRIPTION: str = "FastAPI Admin Backend"
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, ge=1, le=65535)
    RELOAD: bool = False

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    ACCESS_LOG_ENABLED: bool = True

    SQL_ECHO: bool = False
    DB_POOL_SIZE: int = Field(default=10, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0)
    DB_POOL_RECYCLE: int = Field(default=3600, ge=0)

    SECRET_KEY: SecretStr = SecretStr("")
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = False

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("CORS_ORIGINS")
    @classmethod
    def normalize_cors_origins(cls, origins: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(origin.strip() for origin in origins if origin.strip()))
        if not normalized:
            raise ValueError("CORS_ORIGINS 不能为空")
        return normalized

    @model_validator(mode="after")
    def validate_runtime_config(self) -> "Settings":
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL 未配置，请在 .env 文件中设置")

        secret_key = self.SECRET_KEY.get_secret_value()
        if not secret_key:
            raise ValueError("SECRET_KEY 未配置，请在 .env 文件中设置")

        if self.CORS_ALLOW_CREDENTIALS and "*" in self.CORS_ORIGINS:
            raise ValueError("CORS 允许携带凭证时，CORS_ORIGINS 不能使用通配符 *")

        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("生产环境不能开启 DEBUG")
            if self.RELOAD:
                raise ValueError("生产环境不能开启 RELOAD")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("生产环境必须显式配置 CORS_ORIGINS")
            if len(secret_key) < 32 or "change-in-production" in secret_key:
                raise ValueError("生产环境 SECRET_KEY 长度至少为 32 位，且不能使用示例值")

        return self


@lru_cache
def get_settings() -> Settings:
    """获取进程级配置，适用于启动脚本等非请求场景。"""
    return Settings()


def get_database_url() -> str:
    """获取数据库连接地址，Alembic 不需要加载 JWT 等运行配置。"""
    settings = DatabaseSettings()
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL 未配置，请在 .env 文件中设置")
    return settings.DATABASE_URL
