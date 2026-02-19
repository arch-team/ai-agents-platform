"""Admin API 请求模型。"""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.modules.auth.domain.value_objects.role import Role


class AdminCreateUserRequest(BaseModel):
    """管理员创建用户请求。"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    role: str = Role.VIEWER.value

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

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """校验角色值必须是有效的 Role 枚举值。"""
        valid_roles = {r.value for r in Role}
        if v not in valid_roles:
            msg = f"无效的角色值, 允许: {', '.join(sorted(valid_roles))}"
            raise ValueError(msg)
        return v


class ChangeRoleRequest(BaseModel):
    """变更用户角色请求。"""

    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """校验角色值必须是有效的 Role 枚举值。"""
        valid_roles = {r.value for r in Role}
        if v not in valid_roles:
            msg = f"无效的角色值, 允许: {', '.join(sorted(valid_roles))}"
            raise ValueError(msg)
        return v
