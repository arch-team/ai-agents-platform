"""审计日志 API 请求模型测试。

覆盖 src/modules/audit/api/schemas/requests.py 中的 Pydantic 模型。
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.modules.audit.api.schemas.requests import (
    AuditLogExportParams,
    AuditLogQueryParams,
    AuditLogResourceParams,
    AuditLogStatsParams,
)


@pytest.mark.unit
class TestAuditLogQueryParams:
    """AuditLogQueryParams 测试。"""

    def test_defaults(self):
        params = AuditLogQueryParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.category is None
        assert params.action is None
        assert params.actor_id is None

    def test_with_filters(self):
        params = AuditLogQueryParams(
            page=2,
            page_size=50,
            category="agent",
            action="create",
            actor_id=1,
            resource_type="agent",
            resource_id="123",
        )
        assert params.page == 2
        assert params.category == "agent"

    def test_page_must_be_positive(self):
        with pytest.raises(ValidationError):
            AuditLogQueryParams(page=0)

    def test_with_date_range(self):
        start = datetime(2024, 1, 1, tzinfo=UTC)
        end = datetime(2024, 12, 31, tzinfo=UTC)
        params = AuditLogQueryParams(start_date=start, end_date=end)
        assert params.start_date == start
        assert params.end_date == end


@pytest.mark.unit
class TestAuditLogResourceParams:
    """AuditLogResourceParams 测试。"""

    def test_defaults(self):
        params = AuditLogResourceParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_page_size_limit(self):
        with pytest.raises(ValidationError):
            AuditLogResourceParams(page_size=101)


@pytest.mark.unit
class TestAuditLogStatsParams:
    """AuditLogStatsParams 测试。"""

    def test_defaults(self):
        params = AuditLogStatsParams()
        assert params.start_date is None
        assert params.end_date is None

    def test_with_dates(self):
        start = datetime(2024, 1, 1, tzinfo=UTC)
        params = AuditLogStatsParams(start_date=start)
        assert params.start_date == start


@pytest.mark.unit
class TestAuditLogExportParams:
    """AuditLogExportParams 测试。"""

    def test_defaults(self):
        params = AuditLogExportParams()
        assert params.max_rows == 10000
        assert params.category is None

    def test_max_rows_limit(self):
        with pytest.raises(ValidationError):
            AuditLogExportParams(max_rows=200000)

    def test_with_all_fields(self):
        params = AuditLogExportParams(
            category="agent",
            action="create",
            actor_id=1,
            max_rows=5000,
        )
        assert params.category == "agent"
        assert params.max_rows == 5000
