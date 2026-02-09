"""Tool Catalog 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class _ToolEvent(DomainEvent):
    """Tool 事件基类，携带 tool_id 和 creator_id。"""

    tool_id: int = 0
    creator_id: int = 0


@dataclass
class ToolCreatedEvent(_ToolEvent):
    """Tool 创建事件。"""

    name: str = ""
    tool_type: str = ""


@dataclass
class ToolUpdatedEvent(_ToolEvent):
    """Tool 更新事件。"""

    changed_fields: tuple[str, ...] = ()


@dataclass
class ToolDeletedEvent(_ToolEvent):
    """Tool 删除事件。"""


@dataclass
class ToolSubmittedEvent(_ToolEvent):
    """Tool 提交审批事件。"""


@dataclass
class ToolApprovedEvent(_ToolEvent):
    """Tool 审批通过事件。"""

    reviewer_id: int = 0


@dataclass
class ToolRejectedEvent(_ToolEvent):
    """Tool 审批拒绝事件。"""

    reviewer_id: int = 0
    comment: str = ""


@dataclass
class ToolDeprecatedEvent(_ToolEvent):
    """Tool 废弃事件。"""
