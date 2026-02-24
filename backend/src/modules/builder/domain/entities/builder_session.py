"""BuilderSession 领域实体。"""

from typing import Any

from pydantic import ConfigDict

from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.domain.base_entity import PydanticEntity


class BuilderSession(PydanticEntity):
    """Builder 会话实体，管理一次 Agent 构建过程。"""

    model_config = ConfigDict(validate_assignment=True)

    user_id: int
    prompt: str
    status: BuilderStatus = BuilderStatus.PENDING
    generated_config: dict[str, Any] | None = None
    agent_name: str | None = None
    created_agent_id: int | None = None
    department_id: int | None = None  # 所属部门 (允许 NULL, 渐进填充)

    def start_generation(self) -> None:
        """启动生成。PENDING -> GENERATING。"""
        self._require_status(self.status, BuilderStatus.PENDING, BuilderStatus.GENERATING.value)
        self.status = BuilderStatus.GENERATING
        self.touch()

    def complete_generation(self, config: dict[str, Any], name: str) -> None:
        """完成生成。GENERATING -> CONFIRMED。"""
        self._require_status(self.status, BuilderStatus.GENERATING, BuilderStatus.CONFIRMED.value)
        self.status = BuilderStatus.CONFIRMED
        self.generated_config = config
        self.agent_name = name
        self.touch()

    def confirm_creation(self, agent_id: int) -> None:
        """确认创建 Agent。CONFIRMED -> CONFIRMED（设置 agent_id）。"""
        self._require_status(self.status, BuilderStatus.CONFIRMED, "confirm_creation")
        self.created_agent_id = agent_id
        self.touch()

    def cancel(self) -> None:
        """取消会话。PENDING/GENERATING -> CANCELLED。"""
        allowed = frozenset({BuilderStatus.PENDING, BuilderStatus.GENERATING})
        self._require_status(self.status, allowed, BuilderStatus.CANCELLED.value)
        self.status = BuilderStatus.CANCELLED
        self.touch()
