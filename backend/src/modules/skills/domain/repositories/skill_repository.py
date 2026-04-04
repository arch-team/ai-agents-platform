"""Skill 仓库接口。"""

from abc import abstractmethod

from src.modules.skills.domain.entities.skill import Skill
from src.modules.skills.domain.value_objects.skill_category import SkillCategory
from src.shared.domain.repositories import IRepository


class ISkillRepository(IRepository[Skill, int]):
    """Skill 仓库接口。"""

    @abstractmethod
    async def get_by_name(self, name: str) -> Skill | None:
        """按名称查询 Skill。"""

    @abstractmethod
    async def list_published(self, *, offset: int = 0, limit: int = 20) -> list[Skill]:
        """获取已发布的 Skill 列表。"""

    @abstractmethod
    async def list_by_creator(self, creator_id: int, *, offset: int = 0, limit: int = 20) -> list[Skill]:
        """按创建者查询 Skill 列表。"""

    @abstractmethod
    async def list_by_category(self, category: SkillCategory, *, offset: int = 0, limit: int = 20) -> list[Skill]:
        """按分类查询 Skill 列表。"""

    @abstractmethod
    async def search(
        self,
        keyword: str,
        *,
        category: SkillCategory | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Skill]:
        """搜索 Skill。"""

    @abstractmethod
    async def count_by_creator(self, creator_id: int) -> int:
        """按创建者统计 Skill 数量。"""

    @abstractmethod
    async def increment_usage_count(self, skill_id: int) -> None:
        """增加 Skill 使用次数。"""
