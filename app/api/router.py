from fastapi import APIRouter

from app.api.routes import system_routes
from app.core.openapi import COMMON_ERROR_RESPONSES

api_router = APIRouter(prefix="/api", responses=COMMON_ERROR_RESPONSES)
api_router.include_router(system_routes.router)
