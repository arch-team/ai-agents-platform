"""用户领域实体。"""

from datetime import UTC, datetime, timedelta

from pydantic import EmailStr, Field

from src.modules.auth.domain.value_objects.role import Role
from src.modules.auth.domain.value_objects.sso_provider import SsoProvider
from src.shared.domain.base_entity import PydanticEntity


class User(PydanticEntity):
    """用户实体。"""

    email: EmailStr
    hashed_password: str
    name: str = Field(min_length=1, max_length=100)
    role: Role = Role.VIEWER
    is_active: bool = True
    failed_login_count: int = 0
    locked_until: datetime | None = None
    sso_provider: SsoProvider = SsoProvider.INTERNAL
    sso_subject: str | None = None  # SAML NameID / LDAP DN, SSO 用户唯一标识

    @property
    def is_locked(self) -> bool:
        """检查账户是否处于锁定状态。"""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until

    def record_failed_login(self, *, max_attempts: int, lockout_minutes: int) -> None:
        """记录一次登录失败，达到上限时锁定账户。"""
        self.failed_login_count += 1
        if self.failed_login_count >= max_attempts:
            self.locked_until = datetime.now(UTC) + timedelta(minutes=lockout_minutes)
        self.touch()

    def reset_failed_logins(self) -> None:
        """登录成功后重置失败计数和锁定时间。"""
        self.failed_login_count = 0
        self.locked_until = None
        self.touch()

    def activate(self) -> None:
        """激活用户。"""
        self.is_active = True
        self.touch()

    def deactivate(self) -> None:
        """停用用户。"""
        self.is_active = False
        self.touch()

    def change_role(self, new_role: Role) -> None:
        """变更用户角色。"""
        self.role = new_role
        self.touch()
