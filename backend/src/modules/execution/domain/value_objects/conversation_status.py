"""对话状态枚举。"""

from enum import StrEnum


class ConversationStatus(StrEnum):
    """对话状态枚举。"""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
