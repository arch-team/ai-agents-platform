"""insights 模块领域异常。"""

from src.shared.domain.exceptions import DomainError, EntityNotFoundError


class InsightsError(DomainError):
    """insights 模块基础异常。"""

    def __init__(self, message: str = "Insights 错误") -> None:
        super().__init__(message=message, code="INSIGHTS_ERROR")


class InvalidDateRangeError(InsightsError):
    """日期范围无效异常。"""

    def __init__(self) -> None:
        super().__init__(message="日期范围无效: 开始日期不能晚于结束日期")
        self.code = "INVALID_DATE_RANGE"


class UsageRecordNotFoundError(EntityNotFoundError):
    """使用记录不存在。"""

    def __init__(self, record_id: int) -> None:
        super().__init__(entity_type="UsageRecord", entity_id=record_id)
