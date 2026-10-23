from fastapi.testclient import TestClient

from app.core.config import CorsSettings, DocsSettings
from app.main import create_app


def test_health_check_public(make_settings):
    with TestClient(create_app(make_settings())) as client:
        response = client.get("/api/system/health")

    assert response.status_code == 200
    assert response.json()["data"] == {"status": "ok"}


def test_production_disables_api_docs(make_settings):
    with TestClient(create_app(make_settings(environment="production"))) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_docs_use_custom_swagger_cdn(make_settings):
    settings = make_settings()
    with TestClient(create_app(settings)) as client:
        response = client.get("/docs")

    assert response.status_code == 200
    assert settings.docs.SWAGGER_JS_URL in response.text
    assert settings.docs.SWAGGER_CSS_URL in response.text


def test_redoc_can_be_disabled_separately(make_settings):
    settings = make_settings()
    settings.docs = DocsSettings(REDOC_URL="")
    with TestClient(create_app(settings)) as client:
        assert client.get("/redoc").status_code == 404
        assert client.get("/docs").status_code == 200


def test_redoc_can_be_disabled_by_empty_env(make_settings, monkeypatch):
    monkeypatch.setenv("PY_ADMIN_REDOC_URL", "")
    settings = make_settings()
    settings.docs = DocsSettings()
    with TestClient(create_app(settings)) as client:
        assert client.get("/redoc").status_code == 404
        assert client.get("/docs").status_code == 200


def test_unhandled_error_returns_unified_body_with_cors_headers(make_settings):
    app = create_app(make_settings())

    @app.get("/api/boom")
    async def boom():
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/boom", headers={"Origin": "http://example.com"})

    assert response.status_code == 500
    assert response.json()["code"] == 50000
    assert response.headers.get("access-control-allow-origin") == "http://example.com"


def test_cors_origins_accepts_comma_separated_env(monkeypatch):
    monkeypatch.setenv("PY_ADMIN_CORS_ORIGINS", "http://a.com, http://b.com")
    assert CorsSettings().CORS_ORIGINS == ["http://a.com", "http://b.com"]

    monkeypatch.setenv("PY_ADMIN_CORS_ORIGINS", '["http://c.com"]')
    assert CorsSettings().CORS_ORIGINS == ["http://c.com"]


def test_openapi_uses_unified_error_model(make_settings):
    app = create_app(make_settings())
    schema = app.openapi()
    responses = schema["paths"]["/api/system/health"]["get"]["responses"]

    assert "400" in responses
    assert "422" in responses
    assert "500" in responses


def test_request_id_is_returned_and_can_be_provided_by_caller(make_settings):
    with TestClient(create_app(make_settings())) as client:
        generated = client.get("/api/system/health", headers={"Origin": "http://example.com"})
        provided = client.get(
            "/api/system/health",
            headers={"Origin": "http://example.com", "X-Request-ID": "trace-123"},
        )

    assert generated.status_code == 200
    assert generated.headers["x-request-id"]
    assert generated.headers["access-control-expose-headers"] == "X-Request-ID"
    assert provided.headers["x-request-id"] == "trace-123"


def test_internal_http_error_does_not_expose_detail(make_settings):
    from fastapi import HTTPException

    app = create_app(make_settings())

    @app.get("/api/hidden-error")
    async def hidden_error():
        raise HTTPException(status_code=500, detail={"secret": "do-not-return"})

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/hidden-error")

    assert response.status_code == 500
    assert response.json() == {
        "code": 50000,
        "message": "服务器内部错误",
        "data": None,
    }


def test_internal_app_exception_does_not_expose_detail(make_settings):
    from app.core.exceptions import AppException

    app = create_app(make_settings())

    @app.get("/api/hidden-app-error")
    async def hidden_app_error():
        raise AppException(
            message="internal secret",
            http_status=500,
            data={"secret": "do-not-return"},
        )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/hidden-app-error")

    assert response.status_code == 500
    assert response.json() == {
        "code": 50000,
        "message": "\u670d\u52a1\u5668\u5185\u90e8\u9519\u8bef",
        "data": None,
    }
