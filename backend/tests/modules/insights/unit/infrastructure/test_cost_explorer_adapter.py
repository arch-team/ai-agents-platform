"""CostExplorerAdapter 单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.insights.application.interfaces.cost_explorer import (
    PlatformCostSummary,
)
from src.modules.insights.infrastructure.external.cost_explorer_adapter import (
    CostExplorerAdapter,
)


@pytest.mark.unit
class TestCostExplorerAdapter:
    """CostExplorerAdapter.get_bedrock_cost 测试。"""

    @pytest.mark.asyncio
    async def test_normal_response_returns_summary(self) -> None:
        """正常返回: 解析 ResultsByTime 并汇总 total_cost。"""
        # Arrange
        mock_client = MagicMock()
        mock_client.get_cost_and_usage.return_value = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2025-06-01"},
                    "Total": {"UnblendedCost": {"Amount": "12.5", "Unit": "USD"}},
                },
                {
                    "TimePeriod": {"Start": "2025-06-02"},
                    "Total": {"UnblendedCost": {"Amount": "8.3", "Unit": "USD"}},
                },
            ],
        }

        adapter = CostExplorerAdapter()

        with patch(
            "src.modules.insights.infrastructure.external.cost_explorer_adapter._get_ce_client",
            return_value=mock_client,
        ):
            # Act
            result = await adapter.get_bedrock_cost("2025-06-01", "2025-06-03")

        # Assert
        assert isinstance(result, PlatformCostSummary)
        assert result.total_cost == round(12.5 + 8.3, 4)
        assert result.currency == "USD"
        assert len(result.daily_costs) == 2
        assert result.daily_costs[0].date == "2025-06-01"
        assert result.daily_costs[0].amount == 12.5
        assert result.daily_costs[1].date == "2025-06-02"
        assert result.daily_costs[1].amount == 8.3
        assert result.start_date == "2025-06-01"
        assert result.end_date == "2025-06-03"

    @pytest.mark.asyncio
    async def test_empty_results_returns_zero_cost(self) -> None:
        """空数据: ResultsByTime 为空时返回零成本。"""
        # Arrange
        mock_client = MagicMock()
        mock_client.get_cost_and_usage.return_value = {"ResultsByTime": []}

        adapter = CostExplorerAdapter()

        with patch(
            "src.modules.insights.infrastructure.external.cost_explorer_adapter._get_ce_client",
            return_value=mock_client,
        ):
            # Act
            result = await adapter.get_bedrock_cost("2025-06-01", "2025-06-03")

        # Assert
        assert result.total_cost == 0.0
        assert result.daily_costs == ()
        assert result.start_date == "2025-06-01"
        assert result.end_date == "2025-06-03"

    @pytest.mark.asyncio
    async def test_api_exception_degrades_to_zero_cost(self) -> None:
        """API 异常: 降级返回零成本，不阻断业务。"""
        # Arrange
        mock_client = MagicMock()
        mock_client.get_cost_and_usage.side_effect = RuntimeError("AWS API error")

        adapter = CostExplorerAdapter()

        with patch(
            "src.modules.insights.infrastructure.external.cost_explorer_adapter._get_ce_client",
            return_value=mock_client,
        ):
            # Act
            result = await adapter.get_bedrock_cost("2025-06-01", "2025-06-03")

        # Assert — 降级成功, 返回零成本
        assert isinstance(result, PlatformCostSummary)
        assert result.total_cost == 0.0
        assert result.currency == "USD"
        assert result.daily_costs == ()
        assert result.start_date == "2025-06-01"
        assert result.end_date == "2025-06-03"
