"""Agent 领域实体。"""

from pydantic import Field

from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import ValidationError


_ARCHIVABLE = frozenset({AgentStatus.DRAFT, AgentStatus.ACTIVE})


class Agent(PydanticEntity):
    """Agent 实体。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    system_prompt: str = Field(max_length=10000, default="")
    status: AgentStatus = AgentStatus.DRAFT
    owner_id: int
    config: AgentConfig = Field(default_factory=AgentConfig)
    department_id: int | None = None  # 所属部门 (允许 NULL, 渐进填充)

    def activate(self) -> None:
        """激活 Agent。DRAFT -> ACTIVE，需要 system_prompt 非空。"""
        self._require_status(self.status, AgentStatus.DRAFT, AgentStatus.ACTIVE.value)
        if not self.system_prompt.strip():
            raise ValidationError(
                message="激活 Agent 需要设置系统提示词",
                field="system_prompt",
            )
        self.status = AgentStatus.ACTIVE
        self.touch()

    def archive(self) -> None:
        """归档 Agent。DRAFT/ACTIVE -> ARCHIVED，不可逆。"""
        self._require_status(self.status, _ARCHIVABLE, AgentStatus.ARCHIVED.value)
        self.status = AgentStatus.ARCHIVED
        self.touch()
