"""Skills 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class BaseSkillEvent(DomainEvent):
    """Skill 事件基类，携带 skill_id 和 creator_id。"""

    skill_id: int = 0
    creator_id: int = 0


@dataclass
class SkillCreatedEvent(BaseSkillEvent):
    """Skill 创建事件。"""

    name: str = ""


@dataclass
class SkillPublishedEvent(BaseSkillEvent):
    """Skill 发布事件。"""

    version: int = 0


@dataclass
class SkillArchivedEvent(BaseSkillEvent):
    """Skill 归档事件。"""


@dataclass
class SkillDeletedEvent(BaseSkillEvent):
    """Skill 删除事件。"""
