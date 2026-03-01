"""Tool 仓库接口。"""

from abc import abstractmethod

from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.domain.repositories import IRepository


class IToolRepository(IRepository[Tool, int]):
    """Tool 仓库接口。"""

    @abstractmethod
    async def list_by_creator(
        self,
        creator_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tool]: ...

    @abstractmethod
    async def count_by_creator(self, creator_id: int) -> int: ...

    @abstractmethod
    async def get_by_name_and_creator(
        self,
        name: str,
        creator_id: int,
    ) -> Tool | None: ...

    @abstractmethod
    async def list_approved(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tool]: ...

    @abstractmethod
    async def count_approved(self) -> int: ...

    @abstractmethod
    async def list_filtered(
        self,
        *,
        status: ToolStatus | None = None,
        tool_type: ToolType | None = None,
        keyword: str | None = None,
        creator_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tool]: ...

    @abstractmethod
    async def count_filtered(
        self,
        *,
        status: ToolStatus | None = None,
        tool_type: ToolType | None = None,
        keyword: str | None = None,
        creator_id: int | None = None,
    ) -> int: ...

    @abstractmethod
    async def list_by_ids_and_status(self, tool_ids: list[int], status: ToolStatus) -> list[Tool]:
        """按 ID 列表和状态批量查询工具。"""
        ...
