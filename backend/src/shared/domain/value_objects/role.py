"""用户角色值对象 — 跨模块共享定义。"""

from enum import StrEnum


class Role(StrEnum):
    """用户角色枚举。"""

    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
