"""IUsageRecordRepository 接口测试。"""

from abc import abstractmethod

import pytest

from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)
from src.shared.domain.repositories import IRepository


@pytest.mark.unit
class TestIUsageRecordRepository:
    """IUsageRecordRepository 接口定义测试。"""

    def test_inherits_irepository(self) -> None:
        """应继承 IRepository[UsageRecord, int]。"""
        assert issubclass(IUsageRecordRepository, IRepository)

    def test_has_list_by_user_method(self) -> None:
        """应声明 list_by_user 抽象方法。"""
        assert hasattr(IUsageRecordRepository, "list_by_user")
        assert getattr(IUsageRecordRepository.list_by_user, "__isabstractmethod__", False)

    def test_has_list_by_agent_method(self) -> None:
        """应声明 list_by_agent 抽象方法。"""
        assert hasattr(IUsageRecordRepository, "list_by_agent")
        assert getattr(IUsageRecordRepository.list_by_agent, "__isabstractmethod__", False)

    def test_has_list_by_date_range_method(self) -> None:
        """应声明 list_by_date_range 抽象方法。"""
        assert hasattr(IUsageRecordRepository, "list_by_date_range")
        assert getattr(
            IUsageRecordRepository.list_by_date_range, "__isabstractmethod__", False
        )

    def test_has_get_aggregated_stats_method(self) -> None:
        """应声明 get_aggregated_stats 抽象方法。"""
        assert hasattr(IUsageRecordRepository, "get_aggregated_stats")
        assert getattr(
            IUsageRecordRepository.get_aggregated_stats, "__isabstractmethod__", False
        )

    def test_cannot_instantiate(self) -> None:
        """抽象类不应直接实例化。"""
        with pytest.raises(TypeError):
            IUsageRecordRepository()  # type: ignore[abstract]
