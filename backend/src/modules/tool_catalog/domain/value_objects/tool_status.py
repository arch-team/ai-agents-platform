"""Tool 状态枚举。"""

from enum import StrEnum


class ToolStatus(StrEnum):
    """Tool 生命周期状态（审批流）。"""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
