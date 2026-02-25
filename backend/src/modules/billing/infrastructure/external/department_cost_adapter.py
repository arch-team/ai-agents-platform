"""部门成本查询适配器 — 使用 AWS Cost Explorer 按部门 Tag 聚合成本。"""

from __future__ import annotations

import asyncio
from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import boto3
import structlog
from botocore.exceptions import BotoCoreError, ClientError

from src.modules.billing.application.interfaces.cost_service import (
    DepartmentCostPoint,
    DepartmentCostReport,
    IDepartmentCostService,
)
from src.modules.billing.domain.exceptions import BudgetNotFoundError, DepartmentNotFoundError


if TYPE_CHECKING:
    from src.modules.billing.domain.repositories.budget_repository import IBudgetRepository
    from src.modules.billing.domain.repositories.department_repository import IDepartmentRepository


logger = structlog.get_logger(__name__)


@lru_cache
def _get_ce_client() -> Any:  # noqa: ANN401
    """创建 Cost Explorer client 单例 (固定 us-east-1)。"""
    return boto3.client("ce", region_name="us-east-1")


class DepartmentCostAdapter(IDepartmentCostService):
    """部门成本查询适配器 — 通过 Cost Explorer 按 Department Tag 查询成本。"""

    def __init__(
        self,
        department_repo: IDepartmentRepository,
        budget_repo: IBudgetRepository,
    ) -> None:
        self._department_repo = department_repo
        self._budget_repo = budget_repo

    async def get_department_cost_report(
        self,
        department_id: int,
        start_date: str,
        end_date: str,
    ) -> DepartmentCostReport:
        """获取部门成本报告。"""
        # 1. 验证部门存在
        department = await self._department_repo.get_by_id(department_id)
        if department is None:
            raise DepartmentNotFoundError(department_id=department_id)

        # 2. 获取该部门当月预算
        year, month = self._extract_year_month(start_date)
        budget = await self._budget_repo.get_by_department_month(department_id, year, month)
        if budget is None:
            raise BudgetNotFoundError(department_id=department_id)

        # 3. 查询 Cost Explorer
        try:
            response: dict[str, Any] = await asyncio.to_thread(
                self._fetch_department_cost,
                department.code,
                start_date,
                end_date,
            )
        except (ClientError, BotoCoreError):
            logger.exception(
                "cost_explorer_api_failed_for_department",
                department_id=department_id,
                department_code=department.code,
                start_date=start_date,
                end_date=end_date,
            )
            # 降级: 返回零成本报告, 不阻断业务
            return DepartmentCostReport(
                department_id=department_id,
                department_code=department.code,
                department_name=department.name,
                total_cost=0.0,
                budget_amount=budget.budget_amount,
                used_percentage=0.0,
                daily_costs=(),
                start_date=start_date,
                end_date=end_date,
                currency="USD",
            )

        # 4. 解析响应
        daily_costs: list[DepartmentCostPoint] = []
        total = 0.0
        for result in response.get("ResultsByTime", []):
            date = result["TimePeriod"]["Start"]
            # GroupBy 后需要从 Groups 中提取
            for group in result.get("Groups", []):
                # Keys[0] 是 Department Tag 的值
                if group["Keys"][0] == department.code:
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    currency = group["Metrics"]["UnblendedCost"]["Unit"]
                    daily_costs.append(
                        DepartmentCostPoint(
                            date=date,
                            department_code=department.code,
                            amount=amount,
                            currency=currency,
                        ),
                    )
                    total += amount

        used_percentage = (total / budget.budget_amount * 100) if budget.budget_amount > 0 else 0.0

        return DepartmentCostReport(
            department_id=department_id,
            department_code=department.code,
            department_name=department.name,
            total_cost=round(total, 4),
            budget_amount=budget.budget_amount,
            used_percentage=round(used_percentage, 2),
            daily_costs=tuple(daily_costs),
            start_date=start_date,
            end_date=end_date,
            currency="USD",
        )

    @staticmethod
    def _fetch_department_cost(department_code: str, start_date: str, end_date: str) -> dict[str, Any]:
        """同步调用 Cost Explorer API，按 Department Tag 聚合。"""
        client = _get_ce_client()
        result: dict[str, Any] = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "TAG", "Key": "Department"}],
            Filter={
                "Tags": {
                    "Key": "Department",
                    "Values": [department_code],
                },
            },
        )
        return result

    @staticmethod
    def _extract_year_month(date_str: str) -> tuple[int, int]:
        """从日期字符串提取年月 (YYYY-MM-DD -> year, month)。"""
        date = datetime.strptime(date_str, "%Y-%m-%d")  # noqa: DTZ007
        return date.year, date.month
