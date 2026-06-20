from fastapi import APIRouter

from app.api.routes import auth_routes, system_routes, user_routes

# 顶层 API 路由聚合
api_router = APIRouter(prefix="/api")

api_router.include_router(auth_routes.router)
api_router.include_router(user_routes.router)
api_router.include_router(system_routes.router)
