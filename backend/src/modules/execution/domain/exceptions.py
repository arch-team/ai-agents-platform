"""Execution 模块领域异常。"""

from src.shared.domain.exceptions import DomainError, EntityNotFoundError


class ConversationNotFoundError(EntityNotFoundError):
    """对话未找到。"""

    def __init__(self, conversation_id: int) -> None:
        super().__init__(entity_type="Conversation", entity_id=conversation_id)


class MessageNotFoundError(EntityNotFoundError):
    """消息未找到。"""

    def __init__(self, message_id: int) -> None:
        super().__init__(entity_type="Message", entity_id=message_id)


class ConversationNotActiveError(DomainError):
    """对话不在活跃状态。"""

    def __init__(self, conversation_id: int) -> None:
        super().__init__(
            message=f"对话(id={conversation_id}) 不在活跃状态",
            code="CONVERSATION_NOT_ACTIVE",
        )


class AgentNotAvailableError(DomainError):
    """Agent 不可用。"""

    def __init__(self, agent_id: int) -> None:
        super().__init__(
            message=f"Agent(id={agent_id}) 不可用",
            code="AGENT_NOT_AVAILABLE",
        )


class MemoryNotEnabledError(DomainError):
    """Agent 未启用 Memory 功能。"""

    def __init__(self, agent_id: int) -> None:
        super().__init__(
            message=f"Agent(id={agent_id}) 未启用 Memory 功能",
            code="MEMORY_NOT_ENABLED",
        )


# ────────────────────────────────────────────
# 团队执行相关异常
# ────────────────────────────────────────────


class TeamExecutionNotFoundError(EntityNotFoundError):
    """团队执行未找到。"""

    def __init__(self, execution_id: int) -> None:
        super().__init__(entity_type="TeamExecution", entity_id=execution_id)


class TeamExecutionNotCancellableError(DomainError):
    """团队执行不可取消。"""

    def __init__(self, execution_id: int) -> None:
        super().__init__(
            message=f"团队执行(id={execution_id}) 不在可取消状态",
            code="TEAM_EXECUTION_NOT_CANCELLABLE",
        )
