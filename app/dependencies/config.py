from fastapi import Request

from app.core.config import Settings


def get_app_settings(request: Request) -> Settings:
    """获取当前应用实例使用的配置。"""
    return request.app.state.settings
