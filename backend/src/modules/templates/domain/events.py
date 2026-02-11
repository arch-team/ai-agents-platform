"""templates 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class _TemplateEvent(DomainEvent):
    """模板事件基类，携带 template_id。"""

    template_id: int = 0


@dataclass
class TemplateCreatedEvent(_TemplateEvent):
    """模板创建事件。"""

    creator_id: int = 0


@dataclass
class TemplatePublishedEvent(_TemplateEvent):
    """模板发布事件。"""


@dataclass
class TemplateArchivedEvent(_TemplateEvent):
    """模板归档事件。"""


@dataclass
class TemplateInstantiatedEvent(_TemplateEvent):
    """模板实例化事件 — 根据模板创建了新 Agent。"""

    agent_id: int = 0
    instantiated_by: int = 0
