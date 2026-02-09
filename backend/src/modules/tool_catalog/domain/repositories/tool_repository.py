"""Tool 仓库接口。"""

from abc import abstractmethod

from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.domain.repositories import IRepository


class IToolRepository(IRepository[Tool, int]):
    """Tool 仓库接口。"""

    @abstractmethod
    async def list_by_creator(  # noqa: D102
        self,
        creator_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tool]: ...

    @abstractmethod
    async def count_by_creator(self, creator_id: int) -> int: ...  # noqa: D102

    @abstractmethod
    async def get_by_name_and_creator(  # noqa: D102
        self,
        name: str,
        creator_id: int,
    ) -> Tool | None: ...

    @abstractmethod
    async def list_approved(  # noqa: D102
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tool]: ...

    @abstractmethod
    async def count_approved(self) -> int: ...  # noqa: D102

    @abstractmethod
    async def list_filtered(  # noqa: D102
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
    async def count_filtered(  # noqa: D102
        self,
        *,
        status: ToolStatus | None = None,
        tool_type: ToolType | None = None,
        keyword: str | None = None,
        creator_id: int | None = None,
    ) -> int: ...
