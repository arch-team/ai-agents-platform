"""审计事件订阅器实现 — 订阅各模块 DomainEvent 并转换为 AuditLog 记录。"""

from dataclasses import dataclass

import structlog

from src.modules.audit.application.dto.audit_log_dto import CreateAuditLogDTO
from src.modules.audit.application.interfaces.audit_event_subscriber import IAuditEventSubscriber
from src.modules.audit.application.services.audit_service import AuditService
from src.modules.audit.domain.entities.audit_log import AuditAction, AuditCategory
from src.shared.domain.events import DomainEvent


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class EventMapping:
    """事件到审计操作的映射配置。"""

    action: AuditAction
    category: AuditCategory
    resource_type: str
    module: str
    resource_id_field: str
    resource_name_field: str | None = None
    actor_id_field: str = "owner_id"


# 事件类全限定名 → 映射配置
# 使用字符串键避免直接导入其他模块, 保持松耦合
_EVENT_MAPPINGS: dict[str, EventMapping] = {
    # ── Agents 模块 ──
    "AgentCreatedEvent": EventMapping(
        action=AuditAction.CREATE,
        category=AuditCategory.AGENT_MANAGEMENT,
        resource_type="agent",
        module="agents",
        resource_id_field="agent_id",
        resource_name_field="name",
    ),
    "AgentUpdatedEvent": EventMapping(
        action=AuditAction.UPDATE,
        category=AuditCategory.AGENT_MANAGEMENT,
        resource_type="agent",
        module="agents",
        resource_id_field="agent_id",
    ),
    "AgentActivatedEvent": EventMapping(
        action=AuditAction.ACTIVATE,
        category=AuditCategory.AGENT_MANAGEMENT,
        resource_type="agent",
        module="agents",
        resource_id_field="agent_id",
    ),
    "AgentArchivedEvent": EventMapping(
        action=AuditAction.ARCHIVE,
        category=AuditCategory.AGENT_MANAGEMENT,
        resource_type="agent",
        module="agents",
        resource_id_field="agent_id",
    ),
    "AgentDeletedEvent": EventMapping(
        action=AuditAction.DELETE,
        category=AuditCategory.AGENT_MANAGEMENT,
        resource_type="agent",
        module="agents",
        resource_id_field="agent_id",
    ),
    # ── Execution 模块 ──
    "ConversationCreatedEvent": EventMapping(
        action=AuditAction.CREATE,
        category=AuditCategory.EXECUTION,
        resource_type="conversation",
        module="execution",
        resource_id_field="conversation_id",
        actor_id_field="user_id",
    ),
    "TeamExecutionStartedEvent": EventMapping(
        action=AuditAction.EXECUTE,
        category=AuditCategory.EXECUTION,
        resource_type="team_execution",
        module="execution",
        resource_id_field="execution_id",
        actor_id_field="user_id",
    ),
    "TeamExecutionCompletedEvent": EventMapping(
        action=AuditAction.EXECUTE,
        category=AuditCategory.EXECUTION,
        resource_type="team_execution",
        module="execution",
        resource_id_field="execution_id",
        actor_id_field="user_id",
    ),
    "TeamExecutionFailedEvent": EventMapping(
        action=AuditAction.EXECUTE,
        category=AuditCategory.EXECUTION,
        resource_type="team_execution",
        module="execution",
        resource_id_field="execution_id",
        actor_id_field="user_id",
    ),
    # ── Tool Catalog 模块 ──
    "ToolCreatedEvent": EventMapping(
        action=AuditAction.CREATE,
        category=AuditCategory.TOOL_MANAGEMENT,
        resource_type="tool",
        module="tool_catalog",
        resource_id_field="tool_id",
        resource_name_field="name",
        actor_id_field="creator_id",
    ),
    "ToolUpdatedEvent": EventMapping(
        action=AuditAction.UPDATE,
        category=AuditCategory.TOOL_MANAGEMENT,
        resource_type="tool",
        module="tool_catalog",
        resource_id_field="tool_id",
        actor_id_field="creator_id",
    ),
    "ToolDeletedEvent": EventMapping(
        action=AuditAction.DELETE,
        category=AuditCategory.TOOL_MANAGEMENT,
        resource_type="tool",
        module="tool_catalog",
        resource_id_field="tool_id",
        actor_id_field="creator_id",
    ),
    "ToolSubmittedEvent": EventMapping(
        action=AuditAction.SUBMIT,
        category=AuditCategory.TOOL_MANAGEMENT,
        resource_type="tool",
        module="tool_catalog",
        resource_id_field="tool_id",
        actor_id_field="creator_id",
    ),
    "ToolApprovedEvent": EventMapping(
        action=AuditAction.APPROVE,
        category=AuditCategory.TOOL_MANAGEMENT,
        resource_type="tool",
        module="tool_catalog",
        resource_id_field="tool_id",
        actor_id_field="reviewer_id",
    ),
    "ToolRejectedEvent": EventMapping(
        action=AuditAction.REJECT,
        category=AuditCategory.TOOL_MANAGEMENT,
        resource_type="tool",
        module="tool_catalog",
        resource_id_field="tool_id",
        actor_id_field="reviewer_id",
    ),
    "ToolDeprecatedEvent": EventMapping(
        action=AuditAction.DEPRECATE,
        category=AuditCategory.TOOL_MANAGEMENT,
        resource_type="tool",
        module="tool_catalog",
        resource_id_field="tool_id",
        actor_id_field="creator_id",
    ),
    # ── Knowledge 模块 ──
    "KnowledgeBaseCreatedEvent": EventMapping(
        action=AuditAction.CREATE,
        category=AuditCategory.KNOWLEDGE_MANAGEMENT,
        resource_type="knowledge_base",
        module="knowledge",
        resource_id_field="knowledge_base_id",
    ),
    "KnowledgeBaseActivatedEvent": EventMapping(
        action=AuditAction.ACTIVATE,
        category=AuditCategory.KNOWLEDGE_MANAGEMENT,
        resource_type="knowledge_base",
        module="knowledge",
        resource_id_field="knowledge_base_id",
    ),
    "KnowledgeBaseDeletedEvent": EventMapping(
        action=AuditAction.DELETE,
        category=AuditCategory.KNOWLEDGE_MANAGEMENT,
        resource_type="knowledge_base",
        module="knowledge",
        resource_id_field="knowledge_base_id",
    ),
    "DocumentUploadedEvent": EventMapping(
        action=AuditAction.CREATE,
        category=AuditCategory.KNOWLEDGE_MANAGEMENT,
        resource_type="document",
        module="knowledge",
        resource_id_field="document_id",
        resource_name_field="filename",
    ),
    # ── Templates 模块 ──
    "TemplateCreatedEvent": EventMapping(
        action=AuditAction.CREATE,
        category=AuditCategory.TEMPLATE_MANAGEMENT,
        resource_type="template",
        module="templates",
        resource_id_field="template_id",
        actor_id_field="creator_id",
    ),
    "TemplatePublishedEvent": EventMapping(
        action=AuditAction.ACTIVATE,
        category=AuditCategory.TEMPLATE_MANAGEMENT,
        resource_type="template",
        module="templates",
        resource_id_field="template_id",
    ),
    "TemplateArchivedEvent": EventMapping(
        action=AuditAction.ARCHIVE,
        category=AuditCategory.TEMPLATE_MANAGEMENT,
        resource_type="template",
        module="templates",
        resource_id_field="template_id",
    ),
}


class AuditEventSubscriber(IAuditEventSubscriber):
    """审计事件订阅器 — 将 DomainEvent 转换为审计日志记录。"""

    def __init__(self, service: AuditService) -> None:
        self._service = service

    async def handle(self, event: DomainEvent) -> None:
        """处理领域事件，查找映射并记录审计日志。"""
        event_name = type(event).__name__
        mapping = _EVENT_MAPPINGS.get(event_name)
        if mapping is None:
            logger.debug("audit_event_unmapped", event_type=event_name)
            return

        # 从事件属性中提取资源 ID 和操作者 ID
        resource_id = str(getattr(event, mapping.resource_id_field, 0))
        actor_id = getattr(event, mapping.actor_id_field, 0)
        resource_name = (
            getattr(event, mapping.resource_name_field, None)
            if mapping.resource_name_field
            else None
        )

        # 构建额外详情
        details: dict[str, str | int | float | bool | None] | None = None
        if event_name == "TeamExecutionFailedEvent":
            error_msg = getattr(event, "error_message", "")
            if error_msg:
                details = {"error_message": error_msg}
        elif event_name == "AgentUpdatedEvent":
            changed = getattr(event, "changed_fields", ())
            if changed:
                details = {"changed_fields": ",".join(changed)}

        # 确定结果状态
        result = "failure" if event_name == "TeamExecutionFailedEvent" else "success"

        dto = CreateAuditLogDTO(
            actor_id=actor_id,
            actor_name=f"user:{actor_id}",
            action=mapping.action.value,
            category=mapping.category.value,
            resource_type=mapping.resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            module=mapping.module,
            result=result,
            details=details,
        )

        try:
            await self._service.record(dto)
        except Exception:
            logger.exception(
                "audit_event_record_failed",
                event_type=event_name,
                resource_id=resource_id,
            )


def get_event_mappings() -> dict[str, EventMapping]:
    """获取事件映射表（测试用）。"""
    return _EVENT_MAPPINGS
