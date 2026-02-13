"""领域实体基类。"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


def utc_now() -> datetime:
    """获取当前 UTC 时间（唯一实现，Infrastructure 层通过 utils.py 重导出）。"""
    return datetime.now(UTC)


class PydanticEntity(BaseModel):
    """领域实体基类，提供 id、时间戳和相等性语义。"""

    model_config = ConfigDict(validate_assignment=True)

    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def model_post_init(self, context: Any, /) -> None:  # noqa: ANN401, ARG002
        """初始化时间戳。"""
        now = utc_now()
        if self.created_at is None:
            object.__setattr__(self, "created_at", now)
        if self.updated_at is None:
            object.__setattr__(self, "updated_at", self.created_at)

    def require_persisted(self) -> tuple[int, datetime, datetime]:
        """确保实体已持久化（id/created_at/updated_at 不为 None）。

        Returns:
            (id, created_at, updated_at) 三元组，类型均为非 None
        """
        if self.id is None or self.created_at is None or self.updated_at is None:
            msg = f"{type(self).__name__} 缺少必要字段 (id/created_at/updated_at)"
            raise ValueError(msg)
        return self.id, self.created_at, self.updated_at

    def touch(self) -> None:
        """更新 updated_at 时间戳。"""
        self.updated_at = utc_now()

    def _require_status(
        self,
        current: StrEnum,
        allowed: StrEnum | frozenset[StrEnum],
        target: str,
    ) -> None:
        """检查状态转换前置条件。不满足时抛出 InvalidStateTransitionError。"""
        from src.shared.domain.exceptions import InvalidStateTransitionError  # - 避免循环导入

        valid = allowed if isinstance(allowed, frozenset) else frozenset({allowed})
        if current not in valid:
            raise InvalidStateTransitionError(
                entity_type=type(self).__name__,
                current_state=current.value,
                target_state=target if not isinstance(target, StrEnum) else target.value,
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PydanticEntity):
            return NotImplemented
        if self.id is None or other.id is None:
            return self is other
        return self.id == other.id

    def __hash__(self) -> int:
        if self.id is None:
            return id(self)
        return hash(self.id)
