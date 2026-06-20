from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.response import FAIL_CODE
from app.core.security import decode_access_token

# 不需要认证的路径
PUBLIC_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/auth/login",
    "/api/auth/register",
    "/api/system/health",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 全局鉴权中间件"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # CORS 预检请求不做业务鉴权
        if request.method == "OPTIONS":
            return await call_next(request)

        # 公开路径跳过认证
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # 获取 Token
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=401,
                content={"code": FAIL_CODE, "message": "未提供认证 Token", "data": None},
            )

        # 支持 Bearer xxx 和直接 xxx 两种格式
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
        payload = decode_access_token(token)

        if payload is None or not payload.get("sub"):
            return JSONResponse(
                status_code=401,
                content={"code": FAIL_CODE, "message": "Token 无效或已过期", "data": None},
            )

        # 将用户信息存入 request.state
        request.state.user_id = payload.get("sub")
        request.state.username = payload.get("username")

        return await call_next(request)
