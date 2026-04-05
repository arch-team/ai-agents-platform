"""Agents 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class BaseAgentEvent(DomainEvent):
    """Agent 事件基类，携带 agent_id 和 owner_id。"""

    agent_id: int = 0
    owner_id: int = 0


@dataclass
class AgentCreatedEvent(BaseAgentEvent):
    """Agent 创建事件。"""

    name: str = ""


@dataclass
class AgentActivatedEvent(BaseAgentEvent):
    """Agent 激活事件。"""


@dataclass
class AgentArchivedEvent(BaseAgentEvent):
    """Agent 归档事件。"""


@dataclass
class AgentUpdatedEvent(BaseAgentEvent):
    """Agent 更新事件。"""

    changed_fields: tuple[str, ...] = ()


@dataclass
class AgentTestingStartedEvent(BaseAgentEvent):
    """Agent 开始测试事件 — Runtime 已创建。"""

    runtime_arn: str = ""


@dataclass
class AgentGoLiveEvent(BaseAgentEvent):
    """Agent 上线事件 — TESTING → ACTIVE。"""


@dataclass
class AgentTakenOfflineEvent(BaseAgentEvent):
    """Agent 下线事件 — Runtime 已销毁。"""


@dataclass
class AgentDeletedEvent(BaseAgentEvent):
    """Agent 删除事件。"""
