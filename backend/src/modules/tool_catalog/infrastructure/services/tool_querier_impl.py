"""IToolQuerier 实现。基于 tool_catalog Repository 查询已审批工具。"""

from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.repositories.tool_repository import IToolRepository
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.shared.domain.interfaces.tool_querier import ApprovedToolInfo, IToolQuerier


class ToolQuerierImpl(IToolQuerier):
    """基于 tool_catalog Repository 的 IToolQuerier 实现。"""

    def __init__(self, tool_repository: IToolRepository) -> None:
        self._tool_repository = tool_repository

    async def list_approved_tools(self) -> list[ApprovedToolInfo]:
        """返回所有 APPROVED 状态工具的最小信息集。"""
        tools = await self._tool_repository.list_filtered(
            status=ToolStatus.APPROVED,
            offset=0,
            limit=1000,
        )
        return [self._to_approved_tool_info(t) for t in tools]

    @staticmethod
    def _to_approved_tool_info(tool: Tool) -> ApprovedToolInfo:
        """Tool 实体 → ApprovedToolInfo 跨模块 DTO。"""
        if tool.id is None:
            msg = "Tool ID 不能为空"
            raise ValueError(msg)
        return ApprovedToolInfo(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            tool_type=tool.tool_type.value,
            server_url=tool.config.server_url,
            transport=tool.config.transport,
            endpoint_url=tool.config.endpoint_url,
            method=tool.config.method,
            runtime=tool.config.runtime,
            handler=tool.config.handler,
            auth_type=tool.config.auth_type,
        )
