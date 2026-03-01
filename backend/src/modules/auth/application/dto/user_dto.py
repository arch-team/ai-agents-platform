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
    refresh_token: str = ""
    token_type: str = "bearer"  # — OAuth2 标准字段


@dataclass
class RefreshTokenDTO:
    """Refresh Token 请求数据。"""

    refresh_token: str


@dataclass
class UserDTO:
    """用户响应数据 (不含密码)。"""

    id: int
    email: str
    name: str
    role: str
    is_active: bool


@dataclass
class AdminCreateUserDTO:
    """管理员创建用户请求数据。"""

    email: str
    password: str
    name: str
    role: str = "viewer"


@dataclass
class ChangeRoleDTO:
    """变更用户角色请求数据。"""

    user_id: int
    new_role: str


@dataclass
class UserListDTO:
    """用户列表分页响应数据。"""

    items: list[UserDTO]
    total: int
    page: int
    page_size: int
    total_pages: int
