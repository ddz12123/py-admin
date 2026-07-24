import uvicorn

from app.core.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.app.RELOAD,
    )
