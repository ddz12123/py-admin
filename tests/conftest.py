import os
from collections.abc import Callable

import pytest

from app.core.config import AppSettings, CorsSettings, DatabaseSettings, DocsSettings, Settings


@pytest.fixture(scope="session", autouse=True)
def test_database_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    """把测试数据库放到临时目录，避免在仓库根目录留下 .db 文件。"""
    db_file = tmp_path_factory.mktemp("database") / "test.db"
    url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    os.environ["PY_ADMIN_DATABASE_URL"] = url
    os.environ["PY_ADMIN_DEBUG"] = "false"
    # 固定文档相关配置，避免开发者本地 .env 中的自定义值影响测试结果。
    os.environ["PY_ADMIN_DOCS_ENABLED"] = "true"
    os.environ["PY_ADMIN_DOCS_URL"] = "/docs"
    os.environ["PY_ADMIN_REDOC_URL"] = "/redoc"
    os.environ["PY_ADMIN_OPENAPI_URL"] = "/openapi.json"
    return url


@pytest.fixture
def make_settings(test_database_url: str) -> Callable[..., Settings]:
    """构造一份相互独立的测试配置，数据库指向临时文件。"""

    def factory(*, environment: str = "testing") -> Settings:
        return Settings(
            app=AppSettings(ENVIRONMENT=environment, DEBUG=False, RELOAD=False),
            database=DatabaseSettings(DATABASE_URL=test_database_url),
            cors=CorsSettings(CORS_ORIGINS=["http://example.com"]),
            docs=DocsSettings(),
        )

    return factory
