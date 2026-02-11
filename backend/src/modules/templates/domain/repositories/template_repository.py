"""模板仓库接口。"""

from abc import abstractmethod

from src.modules.templates.domain.entities.template import Template
from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)
from src.shared.domain.repositories import IRepository


class ITemplateRepository(IRepository[Template, int]):
    """模板仓库接口。"""

    @abstractmethod
    async def get_by_name(self, name: str) -> Template | None:
        """按名称查询模板。"""

    @abstractmethod
    async def list_published(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """获取已发布的模板列表。"""

    @abstractmethod
    async def list_by_creator(
        self,
        creator_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """按创建者查询模板列表。"""

    @abstractmethod
    async def list_by_category(
        self,
        category: TemplateCategory,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """按分类查询模板列表。"""

    @abstractmethod
    async def search(
        self,
        keyword: str,
        *,
        category: TemplateCategory | None = None,
        tags: list[str] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """搜索模板。"""

    @abstractmethod
    async def increment_usage_count(self, template_id: int) -> None:
        """增加模板使用次数。"""
