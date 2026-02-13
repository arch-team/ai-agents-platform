"""AuditLog 领域实体。"""

from datetime import datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from src.shared.domain.base_entity import PydanticEntity, utc_now


class AuditAction(StrEnum):
    """审计操作类型枚举。"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACTIVATE = "activate"
    ARCHIVE = "archive"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    DEPRECATE = "deprecate"
    EXECUTE = "execute"
    CANCEL = "cancel"
    EXPORT = "export"


class AuditCategory(StrEnum):
    """审计操作分类枚举。"""

    AUTHENTICATION = "authentication"
    AGENT_MANAGEMENT = "agent_management"
    EXECUTION = "execution"
    TOOL_MANAGEMENT = "tool_management"
    KNOWLEDGE_MANAGEMENT = "knowledge_management"
    TEMPLATE_MANAGEMENT = "template_management"
    EVALUATION = "evaluation"
    SYSTEM = "system"


class AuditLog(PydanticEntity):
    """审计日志实体（append-only，只写不改不删）。"""

    model_config = ConfigDict(validate_assignment=True)

    # 操作者信息
    actor_id: int
    actor_name: str = Field(max_length=100)

    # 操作信息
    action: AuditAction
    category: AuditCategory
    resource_type: str = Field(max_length=50)
    resource_id: str = Field(max_length=100)
    resource_name: str | None = Field(default=None, max_length=200)
    module: str = Field(max_length=50)

    # 请求上下文
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=500)
    request_method: str | None = Field(default=None, max_length=10)
    request_path: str | None = Field(default=None, max_length=500)
    status_code: int | None = None

    # 结果
    result: str = Field(default="success", max_length=20)
    error_message: str | None = Field(default=None, max_length=2000)
    details: dict[str, str | int | float | bool | None] | None = None

    # 事件时间
    occurred_at: datetime = Field(default_factory=utc_now)
