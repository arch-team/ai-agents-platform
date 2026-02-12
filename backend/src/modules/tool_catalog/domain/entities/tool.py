"""Tool 领域实体。"""

from datetime import UTC, datetime

from pydantic import Field

from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import ValidationError


class Tool(PydanticEntity):
    """Tool 实体，包含 5 方法审批状态机。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=1000, default="")
    tool_type: ToolType
    version: str = Field(max_length=50, default="1.0.0")
    status: ToolStatus = ToolStatus.DRAFT
    creator_id: int
    config: ToolConfig = Field(default_factory=ToolConfig)
    reviewer_id: int | None = None
    review_comment: str = Field(max_length=1000, default="")
    reviewed_at: datetime | None = None
    allowed_roles: tuple[str, ...] = ("admin", "developer")
    gateway_target_id: str = ""  # AgentCore Gateway Target ID (MCP_SERVER 审批后填充)

    def submit(self) -> None:
        """DRAFT -> PENDING_REVIEW。需 name + description + config 完整。"""
        self._require_status(self.status, ToolStatus.DRAFT, ToolStatus.PENDING_REVIEW.value)
        self._validate_for_submission()
        self.status = ToolStatus.PENDING_REVIEW
        self.touch()

    def approve(self, reviewer_id: int) -> None:
        """PENDING_REVIEW -> APPROVED。"""
        self._require_status(self.status, ToolStatus.PENDING_REVIEW, ToolStatus.APPROVED.value)
        self.status = ToolStatus.APPROVED
        self.reviewer_id = reviewer_id
        self.reviewed_at = datetime.now(UTC)
        self.touch()

    def reject(self, reviewer_id: int, comment: str) -> None:
        """PENDING_REVIEW -> REJECTED。"""
        self._require_status(self.status, ToolStatus.PENDING_REVIEW, ToolStatus.REJECTED.value)
        self.status = ToolStatus.REJECTED
        self.reviewer_id = reviewer_id
        self.review_comment = comment
        self.reviewed_at = datetime.now(UTC)
        self.touch()

    def resubmit(self) -> None:
        """REJECTED -> PENDING_REVIEW。清除审批信息，重新提交。"""
        self._require_status(self.status, ToolStatus.REJECTED, ToolStatus.PENDING_REVIEW.value)
        self._validate_for_submission()
        self.status = ToolStatus.PENDING_REVIEW
        self.reviewer_id = None
        self.review_comment = ""
        self.reviewed_at = None
        self.touch()

    def deprecate(self) -> None:
        """APPROVED -> DEPRECATED。不可逆。"""
        self._require_status(self.status, ToolStatus.APPROVED, ToolStatus.DEPRECATED.value)
        self.status = ToolStatus.DEPRECATED
        self.touch()

    def _validate_for_submission(self) -> None:
        """提交前验证 description 非空和配置完整性。"""
        if not self.description.strip():
            raise ValidationError(
                message="提交 Tool 需要设置描述",
                field="description",
            )
        self._validate_config_for_type()

    def _validate_config_for_type(self) -> None:
        """按 ToolType 验证配置完整性。"""
        if self.tool_type == ToolType.MCP_SERVER:
            if not self.config.server_url.strip():
                raise ValidationError(
                    message="MCP Server 类型的 Tool 需要设置 server_url",
                    field="config.server_url",
                )
        elif self.tool_type == ToolType.API:
            if not self.config.endpoint_url.strip():
                raise ValidationError(
                    message="API 类型的 Tool 需要设置 endpoint_url",
                    field="config.endpoint_url",
                )
        elif self.tool_type == ToolType.FUNCTION:
            if not self.config.runtime.strip():
                raise ValidationError(
                    message="Function 类型的 Tool 需要设置 runtime",
                    field="config.runtime",
                )
            if not self.config.handler.strip():
                raise ValidationError(
                    message="Function 类型的 Tool 需要设置 handler",
                    field="config.handler",
                )
