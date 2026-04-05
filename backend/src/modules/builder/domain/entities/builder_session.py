"""BuilderSession 领域实体。"""

from typing import Any

from pydantic import ConfigDict, Field

from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.domain.base_entity import PydanticEntity


class BuilderSession(PydanticEntity):
    """Builder 会话实体，管理一次 Agent 构建过程。

    V1 字段: prompt, generated_config, agent_name — JSON 配置模式
    V2 字段: messages, template_id, selected_skill_ids, generated_blueprint — Blueprint 模式
    """

    model_config = ConfigDict(validate_assignment=True)

    user_id: int
    prompt: str
    status: BuilderStatus = BuilderStatus.PENDING
    generated_config: dict[str, Any] | None = None
    agent_name: str | None = None
    created_agent_id: int | None = None
    department_id: int | None = None

    # V2: 多轮对话和 Blueprint
    messages: list[dict[str, str]] = Field(default_factory=list)
    template_id: int | None = None
    selected_skill_ids: list[int] = Field(default_factory=list)
    generated_blueprint: dict[str, Any] | None = None

    def start_generation(self) -> None:
        """启动生成。PENDING -> GENERATING。"""
        self._require_status(self.status, BuilderStatus.PENDING, BuilderStatus.GENERATING.value)
        self.status = BuilderStatus.GENERATING
        self.touch()

    def complete_generation(
        self,
        config: dict[str, Any],
        name: str,
        *,
        blueprint: dict[str, Any] | None = None,
    ) -> None:
        """完成生成。GENERATING -> CONFIRMED。

        Args:
            config: V1 JSON 配置 (向后兼容)
            name: Agent 名称
            blueprint: V2 解析后的 Blueprint 结构
        """
        self._require_status(self.status, BuilderStatus.GENERATING, BuilderStatus.CONFIRMED.value)
        self.status = BuilderStatus.CONFIRMED
        self.generated_config = config
        self.agent_name = name
        if blueprint is not None:
            self.generated_blueprint = blueprint
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

    def start_refinement(self) -> None:
        """开始多轮迭代修改。CONFIRMED -> GENERATING。"""
        self._require_status(self.status, BuilderStatus.CONFIRMED, BuilderStatus.GENERATING.value)
        self.status = BuilderStatus.GENERATING
        self.touch()

    def add_message(self, role: str, content: str) -> None:
        """添加消息到对话历史。"""
        self.messages.append({"role": role, "content": content})
        self.touch()
