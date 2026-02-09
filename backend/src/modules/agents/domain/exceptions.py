"""Agents 模块领域异常。"""

from src.shared.domain.exceptions import DuplicateEntityError, EntityNotFoundError


class AgentNotFoundError(EntityNotFoundError):
    """Agent 未找到。"""

    def __init__(self, agent_id: int) -> None:
        super().__init__(entity_type="Agent", entity_id=agent_id)


class AgentNameDuplicateError(DuplicateEntityError):
    """Agent 名称重复。"""

    def __init__(self, name: str) -> None:
        super().__init__(entity_type="Agent", field="name", value=name)
