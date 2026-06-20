from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 项目配置（非敏感，可给默认值）
    PROJECT_NAME: str = Field(
        default="Py-Admin",
        validation_alias=AliasChoices("PY_ADMIN_PROJECT_NAME", "PROJECT_NAME"),
    )
    PROJECT_VERSION: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("PY_ADMIN_PROJECT_VERSION", "PROJECT_VERSION"),
    )
    DESCRIPTION: str = Field(
        default="FastAPI Admin Backend",
        validation_alias=AliasChoices("PY_ADMIN_DESCRIPTION", "DESCRIPTION"),
    )

    # 数据库配置（敏感，必须从 .env 读取）
    DATABASE_URL: str = Field(
        default="",
        validation_alias=AliasChoices("PY_ADMIN_DATABASE_URL", "DATABASE_URL"),
    )

    # JWT 配置（敏感，必须从 .env 读取）
    SECRET_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("PY_ADMIN_SECRET_KEY", "SECRET_KEY"),
    )
    ALGORITHM: str = Field(
        default="HS256",
        validation_alias=AliasChoices("PY_ADMIN_ALGORITHM", "ALGORITHM"),
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        validation_alias=AliasChoices(
            "PY_ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
        ),
    )

    # CORS 配置
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("PY_ADMIN_CORS_ORIGINS", "CORS_ORIGINS"),
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=False,
        validation_alias=AliasChoices("PY_ADMIN_CORS_ALLOW_CREDENTIALS", "CORS_ALLOW_CREDENTIALS"),
    )

    # 调试模式只读取项目前缀变量，避免被系统里的 DEBUG=release 这类通用变量污染
    DEBUG: bool = Field(default=True, validation_alias="PY_ADMIN_DEBUG")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # 启动时验证敏感配置必须已填写
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL 未配置，请在 .env 文件中设置")
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY 未配置，请在 .env 文件中设置")
    return settings


def get_database_url() -> str:
    """获取数据库连接地址（Alembic 迁移只需要数据库配置）"""
    settings = Settings()
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL 未配置，请在 .env 文件中设置")
    return settings.DATABASE_URL
