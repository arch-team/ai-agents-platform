"""使用记录领域实体。"""

from datetime import datetime

from pydantic import ConfigDict

from src.shared.domain.base_entity import PydanticEntity, utc_now


class UsageRecord(PydanticEntity):
    """使用记录实体 — 追加写入的事件日志型实体。"""

    model_config = ConfigDict(validate_assignment=True)

    user_id: int
    agent_id: int
    conversation_id: int
    model_id: str
    tokens_input: int
    tokens_output: int
    estimated_cost: float
    recorded_at: datetime | None = None

    def model_post_init(self, context: object, /) -> None:
        """初始化 recorded_at 默认值。"""
        super().model_post_init(context)
        if self.recorded_at is None:
            object.__setattr__(self, "recorded_at", utc_now())

    @property
    def total_tokens(self) -> int:
        """输入和输出 token 的总和。"""
        return self.tokens_input + self.tokens_output
