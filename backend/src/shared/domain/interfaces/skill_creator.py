"""跨模块 Skill 创建接口。

builder 模块依赖此接口创建 Skill (文件 + DB 记录),
避免直接导入 skills 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CreateSkillRequest:
    """创建 Skill 的跨模块传输对象。"""

    name: str
    description: str
    skill_md: str
    category: str = "general"
    trigger_description: str = ""


@dataclass(frozen=True)
class CreatedSkillInfo:
    """已创建 Skill 的跨模块传输对象。"""

    id: int
    name: str
    file_path: str
    version: int = 1


class ISkillCreator(ABC):
    """跨模块 Skill 创建接口。"""

    @abstractmethod
    async def create_skill(self, request: CreateSkillRequest, creator_id: int) -> CreatedSkillInfo:
        """创建 Skill (DRAFT): 保存 SKILL.md 文件 + 创建数据库记录。"""
        ...

    @abstractmethod
    async def publish_skill(self, skill_id: int, operator_id: int) -> CreatedSkillInfo:
        """发布 Skill: DRAFT → PUBLISHED, 文件系统版本化复制。"""
        ...
