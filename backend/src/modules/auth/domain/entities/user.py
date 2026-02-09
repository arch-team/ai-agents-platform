"""User domain entity."""

from pydantic import EmailStr, Field

from src.modules.auth.domain.value_objects.role import Role
from src.shared.domain.base_entity import PydanticEntity


class User(PydanticEntity):
    """用户实体。"""

    email: EmailStr
    hashed_password: str
    name: str = Field(min_length=1, max_length=100)
    role: Role = Role.VIEWER
    is_active: bool = True

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
