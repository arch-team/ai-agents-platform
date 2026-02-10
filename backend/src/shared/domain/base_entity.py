"""领域实体基类。"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


def utc_now() -> datetime:
    """获取当前 UTC 时间。Domain 层使用此函数，Infrastructure 层使用 shared.infrastructure.utils.utc_now。"""
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

    def touch(self) -> None:
        """更新 updated_at 时间戳。"""
        self.updated_at = utc_now()

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
