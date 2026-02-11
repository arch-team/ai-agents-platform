"""insights 领域异常测试。"""

import pytest

from src.modules.insights.domain.exceptions import (
    InsightsError,
    InvalidDateRangeError,
    UsageRecordNotFoundError,
)
from src.shared.domain.exceptions import DomainError, EntityNotFoundError


@pytest.mark.unit
class TestInsightsError:
    """InsightsError 基础异常测试。"""

    def test_inherits_domain_error(self) -> None:
        error = InsightsError("测试错误")
        assert isinstance(error, DomainError)

    def test_default_code(self) -> None:
        error = InsightsError("测试错误")
        assert error.code == "INSIGHTS_ERROR"

    def test_custom_message(self) -> None:
        error = InsightsError("自定义错误信息")
        assert error.message == "自定义错误信息"


@pytest.mark.unit
class TestInvalidDateRangeError:
    """InvalidDateRangeError 异常测试。"""

    def test_inherits_insights_error(self) -> None:
        error = InvalidDateRangeError()
        assert isinstance(error, InsightsError)

    def test_default_message(self) -> None:
        error = InvalidDateRangeError()
        assert "日期范围" in error.message

    def test_code(self) -> None:
        error = InvalidDateRangeError()
        assert error.code == "INVALID_DATE_RANGE"


@pytest.mark.unit
class TestUsageRecordNotFoundError:
    """UsageRecordNotFoundError 异常测试。"""

    def test_inherits_entity_not_found(self) -> None:
        error = UsageRecordNotFoundError(record_id=42)
        assert isinstance(error, EntityNotFoundError)

    def test_message_contains_id(self) -> None:
        error = UsageRecordNotFoundError(record_id=42)
        assert "42" in error.message

    def test_entity_type(self) -> None:
        error = UsageRecordNotFoundError(record_id=42)
        assert error.entity_type == "UsageRecord"
