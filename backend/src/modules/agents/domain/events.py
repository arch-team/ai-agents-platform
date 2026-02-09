"""Agents 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class AgentCreatedEvent(DomainEvent):
    """Agent 创建事件。"""

    agent_id: int = 0
    owner_id: int = 0
    name: str = ""


@dataclass
class AgentActivatedEvent(DomainEvent):
    """Agent 激活事件。"""

    agent_id: int = 0
    owner_id: int = 0


@dataclass
class AgentArchivedEvent(DomainEvent):
    """Agent 归档事件。"""

    agent_id: int = 0
    owner_id: int = 0


@dataclass
class AgentUpdatedEvent(DomainEvent):
    """Agent 更新事件。"""

    agent_id: int = 0
    owner_id: int = 0
    changed_fields: tuple[str, ...] = ()


@dataclass
class AgentDeletedEvent(DomainEvent):
    """Agent 删除事件。"""

    agent_id: int = 0
    owner_id: int = 0
