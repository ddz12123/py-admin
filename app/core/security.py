import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def _password_digest(password: str) -> bytes:
    """将密码压缩到 bcrypt 72 字节限制以内。"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")


def _check_bcrypt(password: bytes, hashed_password: bytes) -> bool:
    try:
        return bcrypt.checkpw(password, hashed_password)
    except ValueError:
        return False


def hash_password(password: str) -> str:
    """对密码进行哈希"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(_password_digest(password), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    hashed_password_bytes = hashed_password.encode("utf-8")
    if _check_bcrypt(_password_digest(plain_password), hashed_password_bytes):
        return True

    # 兼容旧版本直接 bcrypt 的存量密码；bcrypt 只使用前 72 个字节。
    legacy_password = plain_password.encode("utf-8")[:72]
    return _check_bcrypt(legacy_password, hashed_password_bytes)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
