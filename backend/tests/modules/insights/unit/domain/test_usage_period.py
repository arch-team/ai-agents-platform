"""UsagePeriod 枚举单元测试。"""

import pytest

from src.modules.insights.domain.value_objects.usage_period import UsagePeriod


@pytest.mark.unit
class TestUsagePeriod:
    """UsagePeriod 枚举测试。"""

    def test_daily_value(self) -> None:
        assert UsagePeriod.DAILY == "daily"

    def test_weekly_value(self) -> None:
        assert UsagePeriod.WEEKLY == "weekly"

    def test_monthly_value(self) -> None:
        assert UsagePeriod.MONTHLY == "monthly"

    def test_is_str_enum(self) -> None:
        assert isinstance(UsagePeriod.DAILY, str)

    def test_all_members(self) -> None:
        members = set(UsagePeriod)
        assert members == {UsagePeriod.DAILY, UsagePeriod.WEEKLY, UsagePeriod.MONTHLY}
