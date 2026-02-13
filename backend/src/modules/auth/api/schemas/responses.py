"""认证 API 响应模型。"""

from pydantic import BaseModel


class UserResponse(BaseModel):
    """用户信息响应。"""

    id: int
    email: str
    name: str
    role: str
    is_active: bool


class TokenResponse(BaseModel):
    """JWT Token 响应。"""

    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """通用消息响应。"""

    message: str
