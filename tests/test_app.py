from fastapi.testclient import TestClient

from app.core.config import AppSettings, CorsSettings, DatabaseSettings, DocsSettings, Settings
from app.main import create_app


def make_settings(*, environment: str = "testing") -> Settings:
    return Settings(
        app=AppSettings(ENVIRONMENT=environment, DEBUG=False, RELOAD=False),
        database=DatabaseSettings(DATABASE_URL="sqlite+aiosqlite:///./test.db"),
        cors=CorsSettings(CORS_ORIGINS=["http://example.com"]),
        docs=DocsSettings(),
    )


def test_health_check_public():
    with TestClient(create_app(make_settings())) as client:
        response = client.get("/api/system/health")

    assert response.status_code == 200
    assert response.json()["data"] == {"status": "ok"}


def test_production_disables_api_docs():
    with TestClient(create_app(make_settings(environment="production"))) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_openapi_uses_unified_error_model():
    app = create_app(make_settings())
    schema = app.openapi()
    responses = schema["paths"]["/api/system/health"]["get"]["responses"]

    assert "400" in responses
    assert "422" in responses
    assert "500" in responses
