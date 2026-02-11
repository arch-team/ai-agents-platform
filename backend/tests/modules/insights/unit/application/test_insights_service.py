"""InsightsService 应用服务单元测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.insights.application.dto.insights_dto import (
    CreateUsageRecordDTO,
    PagedUsageRecordDTO,
    UsageRecordDTO,
    UsageSummaryDTO,
)
from src.modules.insights.application.interfaces.cost_calculator import ICostCalculator
from src.modules.insights.application.services.insights_service import InsightsService
from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.modules.insights.domain.exceptions import (
    InvalidDateRangeError,
    UsageRecordNotFoundError,
)
from src.modules.insights.domain.repositories.usage_record_repository import (
    IUsageRecordRepository,
)
from src.modules.insights.domain.value_objects.cost_breakdown import CostBreakdown


def _make_record(
    record_id: int = 1,
    user_id: int = 10,
    agent_id: int = 5,
    conversation_id: int = 100,
    model_id: str = "anthropic.claude-sonnet-4-20250514",
    tokens_input: int = 1000,
    tokens_output: int = 500,
    estimated_cost: float = 0.0105,
) -> UsageRecord:
    """创建测试用 UsageRecord。"""
    record = UsageRecord(
        user_id=user_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        model_id=model_id,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        estimated_cost=estimated_cost,
    )
    object.__setattr__(record, "id", record_id)
    return record


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=IUsageRecordRepository)


@pytest.fixture
def mock_calculator() -> MagicMock:
    calc = MagicMock(spec=ICostCalculator)
    calc.calculate_cost.return_value = CostBreakdown(
        tokens_input=1000,
        tokens_output=500,
        input_cost=0.003,
        output_cost=0.0075,
        total_cost=0.0105,
        model_id="anthropic.claude-sonnet-4-20250514",
    )
    return calc


@pytest.fixture
def service(mock_repo: AsyncMock, mock_calculator: MagicMock) -> InsightsService:
    return InsightsService(
        usage_repo=mock_repo,
        cost_calculator=mock_calculator,
    )


@pytest.mark.unit
class TestRecordUsage:
    """record_usage 测试。"""

    @pytest.mark.asyncio
    async def test_creates_record_and_returns_dto(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
        mock_calculator: MagicMock,
    ) -> None:
        mock_repo.create.return_value = _make_record()

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
            result = await service.record_usage(dto)

        assert isinstance(result, UsageRecordDTO)
        assert result.id == 1
        assert result.user_id == 10
        assert result.estimated_cost == 0.0105
        mock_calculator.calculate_cost.assert_called_once_with(
            "anthropic.claude-sonnet-4-20250514", 1000, 500,
        )
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_publishes_event(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.create.return_value = _make_record()

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
            await service.record_usage(dto)
            mock_bus.publish_async.assert_called_once()


@pytest.mark.unit
class TestGetUsageRecord:
    """get_usage_record 测试。"""

    @pytest.mark.asyncio
    async def test_returns_dto(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.get_by_id.return_value = _make_record(record_id=42)
        result = await service.get_usage_record(42)
        assert isinstance(result, UsageRecordDTO)
        assert result.id == 42

    @pytest.mark.asyncio
    async def test_not_found_raises(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.get_by_id.return_value = None
        with pytest.raises(UsageRecordNotFoundError):
            await service.get_usage_record(999)


@pytest.mark.unit
class TestListUsageRecords:
    """list_usage_records 测试。"""

    @pytest.mark.asyncio
    async def test_list_all(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.list.return_value = [_make_record(record_id=1), _make_record(record_id=2)]
        mock_repo.count.return_value = 2

        result = await service.list_usage_records(page=1, page_size=20)
        assert isinstance(result, PagedUsageRecordDTO)
        assert len(result.items) == 2
        assert result.total == 2
        mock_repo.list.assert_called_once_with(offset=0, limit=20)

    @pytest.mark.asyncio
    async def test_list_by_user(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.list_by_user.return_value = [_make_record()]
        mock_repo.count.return_value = 1

        result = await service.list_usage_records(user_id=10, page=1, page_size=20)
        assert len(result.items) == 1
        mock_repo.list_by_user.assert_called_once_with(10, offset=0, limit=20)

    @pytest.mark.asyncio
    async def test_list_by_agent(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.list_by_agent.return_value = [_make_record()]
        mock_repo.count.return_value = 1

        result = await service.list_usage_records(agent_id=5, page=1, page_size=20)
        assert len(result.items) == 1
        mock_repo.list_by_agent.assert_called_once_with(5, offset=0, limit=20)

    @pytest.mark.asyncio
    async def test_pagination_offset(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.list.return_value = []
        mock_repo.count.return_value = 0

        await service.list_usage_records(page=3, page_size=10)
        mock_repo.list.assert_called_once_with(offset=20, limit=10)


@pytest.mark.unit
class TestGetUsageSummary:
    """get_usage_summary 测试。"""

    @pytest.mark.asyncio
    async def test_returns_summary(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.get_aggregated_stats.return_value = {
            "total_tokens": 15000,
            "total_cost": 0.05,
            "conversation_count": 10,
            "record_count": 25,
        }

        result = await service.get_usage_summary(user_id=10, period="daily")
        assert isinstance(result, UsageSummaryDTO)
        assert result.total_tokens == 15000
        assert result.total_cost == 0.05
        assert result.conversation_count == 10
        assert result.record_count == 25
        assert result.period == "daily"

    @pytest.mark.asyncio
    async def test_invalid_date_range_raises(
        self,
        service: InsightsService,
    ) -> None:
        start = datetime(2025, 6, 1, tzinfo=UTC)
        end = datetime(2025, 1, 1, tzinfo=UTC)

        with pytest.raises(InvalidDateRangeError):
            await service.get_usage_summary(start=start, end=end)

    @pytest.mark.asyncio
    async def test_valid_date_range_passes(
        self,
        service: InsightsService,
        mock_repo: AsyncMock,
    ) -> None:
        mock_repo.get_aggregated_stats.return_value = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "conversation_count": 0,
            "record_count": 0,
        }

        start = datetime(2025, 1, 1, tzinfo=UTC)
        end = datetime(2025, 6, 1, tzinfo=UTC)

        result = await service.get_usage_summary(start=start, end=end)
        assert isinstance(result, UsageSummaryDTO)
