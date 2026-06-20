# 所有模型统一导入，新增表在这里加
from app.models.user import User  # noqa: F401

__all__ = ["User"]
