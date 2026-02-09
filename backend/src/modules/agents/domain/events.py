"""Agents 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class _AgentEvent(DomainEvent):
    """Agent 事件基类，携带 agent_id 和 owner_id。"""

    agent_id: int = 0
    owner_id: int = 0


@dataclass
class AgentCreatedEvent(_AgentEvent):
    """Agent 创建事件。"""

    name: str = ""


@dataclass
class AgentActivatedEvent(_AgentEvent):
    """Agent 激活事件。"""


@dataclass
class AgentArchivedEvent(_AgentEvent):
    """Agent 归档事件。"""


@dataclass
class AgentUpdatedEvent(_AgentEvent):
    """Agent 更新事件。"""

    changed_fields: tuple[str, ...] = ()


@dataclass
class AgentDeletedEvent(_AgentEvent):
    """Agent 删除事件。"""
