"""AgentCore Gateway 工具同步事件处理器。

监听 ToolApprovedEvent → 注册 MCP_SERVER 工具到 Gateway
监听 ToolDeprecatedEvent → 从 Gateway 移除工具
"""

import structlog

from src.modules.tool_catalog.application.interfaces.gateway_sync import IGatewaySyncService
from src.modules.tool_catalog.domain.events import ToolApprovedEvent, ToolDeprecatedEvent
from src.modules.tool_catalog.domain.repositories.tool_repository import IToolRepository


logger = structlog.get_logger(__name__)


async def handle_tool_approved(
    event: ToolApprovedEvent,
    *,
    repo: IToolRepository,
    gateway_sync: IGatewaySyncService,
) -> None:
    """工具审批通过后，将 MCP_SERVER 类型工具注册到 Gateway。"""
    tool = await repo.get_by_id(event.tool_id)
    if tool is None:
        logger.warning("gateway_sync_tool_not_found", tool_id=event.tool_id)
        return

    if tool.tool_type.value != "mcp_server":
        logger.debug("gateway_sync_skip_non_mcp", tool_id=event.tool_id, tool_type=tool.tool_type.value)
        return

    target_id = await gateway_sync.register_tool(
        tool_id=event.tool_id,
        tool_name=tool.name,
        description=tool.description,
        server_url=tool.config.server_url,
        transport=tool.config.transport,
    )

    if target_id:
        tool.gateway_target_id = target_id
        await repo.update(tool)
        logger.info("gateway_sync_registered", tool_id=event.tool_id, target_id=target_id)


async def handle_tool_deprecated(
    event: ToolDeprecatedEvent,
    *,
    repo: IToolRepository,
    gateway_sync: IGatewaySyncService,
) -> None:
    """工具废弃后，从 Gateway 移除。"""
    tool = await repo.get_by_id(event.tool_id)
    if tool is None:
        logger.warning("gateway_sync_tool_not_found", tool_id=event.tool_id)
        return

    if not tool.gateway_target_id:
        logger.debug("gateway_sync_skip_no_target", tool_id=event.tool_id)
        return

    await gateway_sync.unregister_tool(
        tool_id=event.tool_id,
        target_id=tool.gateway_target_id,
    )

    tool.gateway_target_id = ""
    await repo.update(tool)
    logger.info("gateway_sync_unregistered", tool_id=event.tool_id)
