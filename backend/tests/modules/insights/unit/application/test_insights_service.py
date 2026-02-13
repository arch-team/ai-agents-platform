"""InsightsService 应用服务单元测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.insights.application.dto.insights_dto import (
    CreateUsageRecordDTO,
    UsageRecordDTO,
    UsageSummaryDTO,
)
from src.shared.application.dtos import PagedResult
from src.modules.insights.application.services.insights_service import InsightsService
from src.modules.insights.domain.exceptions import (
    InvalidDateRangeError,
    UsageRecordNotFoundError,
)

from tests.modules.insights.conftest import make_usage_record


@pytest.mark.unit
class TestRecordUsage:
    """record_usage 测试。"""

    @pytest.mark.asyncio
    async def test_creates_record_and_returns_dto(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
        mock_cost_calculator: MagicMock,
    ) -> None:
        mock_usage_repo.create.return_value = make_usage_record()

        dto = CreateUsageRecordDTO(
            user_id=10,
            agent_id=5,
            conversation_id=100,
            model_id="anthropic.claude-sonnet-4-20250514",
            tokens_input=1000,
            tokens_output=500,
        )

        with patch("src.modules.insights.application.services.insights_service.event_bus") as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await insights_service.record_usage(dto)

        assert isinstance(result, UsageRecordDTO)
        assert result.id == 1
        assert result.user_id == 10
        assert result.estimated_cost == 0.0105
        mock_cost_calculator.calculate_cost.assert_called_once_with(
            "anthropic.claude-sonnet-4-20250514", 1000, 500,
        )
        mock_usage_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_record_without_conversation(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
        mock_cost_calculator: MagicMock,
    ) -> None:
        """团队执行场景: conversation_id 为 None 时可正常创建。"""
        mock_usage_repo.create.return_value = make_usage_record(conversation_id=None)

        dto = CreateUsageRecordDTO(
            user_id=10,
            agent_id=5,
            model_id="anthropic.claude-sonnet",
            tokens_input=800,
            tokens_output=300,
        )

        with patch("src.modules.insights.application.services.insights_service.event_bus") as mock_bus:
            mock_bus.publish_async = AsyncMock()
            result = await insights_service.record_usage(dto)

        assert isinstance(result, UsageRecordDTO)
        assert result.conversation_id is None
        mock_usage_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_publishes_event(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        mock_usage_repo.create.return_value = make_usage_record()

        dto = CreateUsageRecordDTO(
            user_id=10,
            agent_id=5,
            conversation_id=100,
            model_id="model-a",
            tokens_input=1000,
            tokens_output=500,
        )

        with patch("src.modules.insights.application.services.insights_service.event_bus") as mock_bus:
            mock_bus.publish_async = AsyncMock()
            await insights_service.record_usage(dto)
            mock_bus.publish_async.assert_called_once()


@pytest.mark.unit
class TestGetUsageRecord:
    """get_usage_record 测试。"""

    @pytest.mark.asyncio
    async def test_returns_dto(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        mock_usage_repo.get_by_id.return_value = make_usage_record(record_id=42)
        result = await insights_service.get_usage_record(42)
        assert isinstance(result, UsageRecordDTO)
        assert result.id == 42

    @pytest.mark.asyncio
    async def test_not_found_raises(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        mock_usage_repo.get_by_id.return_value = None
        with pytest.raises(UsageRecordNotFoundError):
            await insights_service.get_usage_record(999)


@pytest.mark.unit
class TestListUsageRecords:
    """list_usage_records 测试。"""

    @pytest.mark.asyncio
    async def test_list_all(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        mock_usage_repo.list.return_value = [make_usage_record(record_id=1), make_usage_record(record_id=2)]
        mock_usage_repo.count.return_value = 2

        result = await insights_service.list_usage_records(page=1, page_size=20)
        assert isinstance(result, PagedResult)
        assert len(result.items) == 2
        assert result.total == 2
        mock_usage_repo.list.assert_called_once_with(offset=0, limit=20)

    @pytest.mark.asyncio
    async def test_list_by_user(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        mock_usage_repo.list_by_user.return_value = [make_usage_record()]
        mock_usage_repo.count_by_user.return_value = 1

        result = await insights_service.list_usage_records(user_id=10, page=1, page_size=20)
        assert len(result.items) == 1
        assert result.total == 1
        mock_usage_repo.list_by_user.assert_called_once_with(10, offset=0, limit=20)
        mock_usage_repo.count_by_user.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_list_by_agent(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        mock_usage_repo.list_by_agent.return_value = [make_usage_record()]
        mock_usage_repo.count_by_agent.return_value = 1

        result = await insights_service.list_usage_records(agent_id=5, page=1, page_size=20)
        assert len(result.items) == 1
        assert result.total == 1
        mock_usage_repo.list_by_agent.assert_called_once_with(5, offset=0, limit=20)
        mock_usage_repo.count_by_agent.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_pagination_offset(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        mock_usage_repo.list.return_value = []
        mock_usage_repo.count.return_value = 0

        await insights_service.list_usage_records(page=3, page_size=10)
        mock_usage_repo.list.assert_called_once_with(offset=20, limit=10)


@pytest.mark.unit
class TestGetUsageSummary:
    """get_usage_summary 测试。"""

    @pytest.mark.asyncio
    async def test_returns_summary(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        from src.modules.insights.domain.value_objects.aggregated_stats import AggregatedStats

        mock_usage_repo.get_aggregated_stats.return_value = AggregatedStats(
            total_tokens=15000,
            total_cost=0.05,
            conversation_count=10,
            record_count=25,
        )

        result = await insights_service.get_usage_summary(user_id=10, period="daily")
        assert isinstance(result, UsageSummaryDTO)
        assert result.total_tokens == 15000
        assert result.total_cost == 0.05
        assert result.conversation_count == 10
        assert result.record_count == 25
        assert result.period == "daily"

    @pytest.mark.asyncio
    async def test_invalid_date_range_raises(
        self,
        insights_service: InsightsService,
    ) -> None:
        start = datetime(2025, 6, 1, tzinfo=UTC)
        end = datetime(2025, 1, 1, tzinfo=UTC)

        with pytest.raises(InvalidDateRangeError):
            await insights_service.get_usage_summary(start=start, end=end)

    @pytest.mark.asyncio
    async def test_valid_date_range_passes(
        self,
        insights_service: InsightsService,
        mock_usage_repo: AsyncMock,
    ) -> None:
        from src.modules.insights.domain.value_objects.aggregated_stats import AggregatedStats

        mock_usage_repo.get_aggregated_stats.return_value = AggregatedStats(
            total_tokens=0,
            total_cost=0.0,
            conversation_count=0,
            record_count=0,
        )

        start = datetime(2025, 1, 1, tzinfo=UTC)
        end = datetime(2025, 6, 1, tzinfo=UTC)

        result = await insights_service.get_usage_summary(start=start, end=end)
        assert isinstance(result, UsageSummaryDTO)
