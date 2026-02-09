"""用户相关 DTO。"""

from dataclasses import dataclass


@dataclass
class CreateUserDTO:
    """创建用户请求数据。"""

    email: str
    password: str
    name: str


@dataclass
class LoginDTO:
    """登录请求数据。"""

    email: str
    password: str


@dataclass
class TokenDTO:
    """JWT Token 响应数据。"""

    access_token: str
    token_type: str = "bearer"  # noqa: S105


@dataclass
class UserDTO:
    """用户响应数据 (不含密码)。"""

    id: int
    email: str
    name: str
    role: str
    is_active: bool
