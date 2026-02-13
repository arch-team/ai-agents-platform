"""insights 模块领域异常。"""

from src.shared.domain.exceptions import DomainError, EntityNotFoundError


class InsightsError(DomainError):
    """insights 模块基础异常。"""

    def __init__(self, message: str = "Insights 错误", code: str = "INSIGHTS_ERROR") -> None:
        super().__init__(message=message, code=code)


class InvalidDateRangeError(InsightsError):
    """日期范围无效异常。"""

    def __init__(self) -> None:
        super().__init__(
            message="日期范围无效: 开始日期不能晚于结束日期",
            code="INVALID_DATE_RANGE",
        )


class UsageRecordNotFoundError(InsightsError, EntityNotFoundError):
    """使用记录不存在。"""

    def __init__(self, record_id: int) -> None:
        EntityNotFoundError.__init__(self, entity_type="UsageRecord", entity_id=record_id)
