"""认证 API 请求模型。"""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """用户注册请求。"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """密码复杂度校验: 至少包含大写字母、小写字母和数字。"""
        if not re.search(r"[A-Z]", v):
            msg = "密码必须包含至少一个大写字母"
            raise ValueError(msg)
        if not re.search(r"[a-z]", v):
            msg = "密码必须包含至少一个小写字母"
            raise ValueError(msg)
        if not re.search(r"[0-9]", v):
            msg = "密码必须包含至少一个数字"
            raise ValueError(msg)
        return v


class LoginRequest(BaseModel):
    """用户登录请求。"""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh Token 请求（登出复用同一结构）。"""

    refresh_token: str


# 登出请求与 Refresh Token 请求结构完全一致, 复用同一 Schema
LogoutRequest = RefreshTokenRequest


class SsoInitRequest(BaseModel):
    """SSO 登录发起请求。"""

    return_url: str = Field(description="SSO 登录成功后的回调 URL")
