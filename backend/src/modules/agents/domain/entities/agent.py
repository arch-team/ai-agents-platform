"""Agent 领域实体。"""

from pydantic import Field

from src.modules.agents.domain.value_objects.agent_config import AgentConfig
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import ValidationError


_ACTIVATABLE = frozenset({AgentStatus.DRAFT, AgentStatus.TESTING})
_ARCHIVABLE = frozenset({AgentStatus.DRAFT, AgentStatus.TESTING, AgentStatus.ACTIVE})


class Agent(PydanticEntity):
    """Agent 实体。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    system_prompt: str = Field(max_length=10000, default="")
    status: AgentStatus = AgentStatus.DRAFT
    owner_id: int
    config: AgentConfig = Field(default_factory=AgentConfig)
    department_id: int | None = None
    blueprint_id: int | None = None

    def start_testing(self) -> None:
        """开始测试。DRAFT → TESTING (Blueprint 模式, 创建 Runtime)。"""
        self._require_status(self.status, AgentStatus.DRAFT, AgentStatus.TESTING.value)
        self.status = AgentStatus.TESTING
        self.touch()

    def activate(self) -> None:
        """激活 Agent。

        TESTING → ACTIVE (Blueprint 上线, 无需 system_prompt)
        DRAFT → ACTIVE (V1 兼容, 需要 system_prompt 非空)
        """
        self._require_status(self.status, _ACTIVATABLE, AgentStatus.ACTIVE.value)
        if self.status == AgentStatus.DRAFT and not self.system_prompt.strip():
            raise ValidationError(
                message="激活 Agent 需要设置系统提示词",
                field="system_prompt",
            )
        self.status = AgentStatus.ACTIVE
        self.touch()

    def archive(self) -> None:
        """归档 Agent。DRAFT/TESTING/ACTIVE → ARCHIVED，不可逆。"""
        self._require_status(self.status, _ARCHIVABLE, AgentStatus.ARCHIVED.value)
        self.status = AgentStatus.ARCHIVED
        self.touch()
