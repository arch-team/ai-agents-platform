"""User role value object."""

from enum import StrEnum


class Role(StrEnum):
    """用户角色枚举。"""

    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
