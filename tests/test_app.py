from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.routes import auth_routes
from app.core.exceptions import AppException
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.main import app
from app.middlewares.auth_middleware import is_public_path
from app.schemas.auth_schema import RegisterRequest


async def _override_db():
    yield None


def test_health_check_public():
    client = TestClient(app)

    response = client.get("/api/system/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok"},
    }


def test_public_route_with_trailing_slash_is_not_auth_blocked():
    client = TestClient(app)

    response = client.get("/api/system/health/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/api/system/health"


def test_protected_route_requires_token():
    client = TestClient(app)

    response = client.get("/api/users")

    assert response.status_code == 401
    assert response.json()["message"] == "未提供认证 Token"


def test_auth_error_response_has_cors_headers():
    client = TestClient(app)

    response = client.get(
        "/api/users",
        headers={"Origin": "http://example.com"},
    )

    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == "*"


def test_login_business_error_returns_400(monkeypatch):
    async def fake_login(db, req):
        raise AppException(message="账号已被禁用")

    monkeypatch.setattr(auth_routes.auth_service, "login", fake_login)
    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)

    try:
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "123456"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {
        "code": 1,
        "message": "账号已被禁用",
        "data": None,
    }


def test_register_success_data_matches_openapi(monkeypatch):
    async def fake_register(db, req):
        return None

    monkeypatch.setattr(auth_routes.auth_service, "register", fake_register)
    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)

    try:
        response = client.post(
            "/api/auth/register",
            json={"username": "admin", "password": "123456"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "注册成功",
        "data": {},
    }


def test_username_is_validated_after_strip():
    try:
        RegisterRequest(username=" a ", password="123456")
    except ValidationError as exc:
        assert exc.errors()[0]["msg"] == "Value error, 用户名长度不能少于2个字符"
    else:
        raise AssertionError("用户名 trim 后长度不足时应校验失败")


def test_max_length_password_hashes_and_verifies():
    password = "p" * 128

    hashed = hash_password(password)

    assert verify_password(password, hashed)
    assert not verify_password(password + "x", hashed)


def test_legacy_bcrypt_password_hash_still_verifies():
    import bcrypt

    password = "legacy-password"
    legacy_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    assert verify_password(password, legacy_hash)


def test_public_path_matching_does_not_overmatch():
    assert is_public_path("/docs")
    assert is_public_path("/docs/")
    assert is_public_path("/docs/oauth2-redirect")
    assert is_public_path("/api/system/health/")
    assert not is_public_path("/docs-extra")


def test_openapi_marks_only_protected_routes():
    schema = app.openapi()

    assert schema["paths"]["/api/auth/login"]["post"].get("security") is None
    assert schema["paths"]["/api/auth/register"]["post"].get("security") is None
    assert schema["paths"]["/api/system/health"]["get"].get("security") is None
    assert schema["paths"]["/api/users"]["get"]["security"] == [{"BearerAuth": []}]
    assert schema["paths"]["/api/users/me"]["get"]["security"] == [{"BearerAuth": []}]
