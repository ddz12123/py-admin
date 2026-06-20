from pydantic import BaseModel, Field, field_validator


class AuthBase(BaseModel):
    """认证请求基类"""

    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("用户名不能为空")
        if len(v) < 2:
            raise ValueError("用户名长度不能少于2个字符")
        if len(v) > 50:
            raise ValueError("用户名长度不能超过50个字符")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if v.strip() != v:
            raise ValueError("密码不能包含首尾空格")
        return v


class LoginRequest(AuthBase):
    """登录请求"""

    model_config = {"json_schema_extra": {"examples": [{"username": "admin", "password": "123456"}]}}


class RegisterRequest(AuthBase):
    """注册请求"""

    model_config = {"json_schema_extra": {"examples": [{"username": "admin", "password": "123456"}]}}


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="JWT Token")
    token_type: str = Field(default="bearer", description="Token 类型")
