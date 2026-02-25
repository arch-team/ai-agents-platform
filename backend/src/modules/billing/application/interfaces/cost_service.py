"""部门成本查询服务接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DepartmentCostPoint:
    """部门单日成本数据点。"""

    date: str
    department_code: str
    amount: float
    currency: str = "USD"


@dataclass(frozen=True)
class DepartmentCostReport:
    """部门成本报告。"""

    department_id: int
    department_code: str
    department_name: str
    total_cost: float
    budget_amount: float  # 当月预算
    used_percentage: float  # 成本/预算比率
    daily_costs: tuple[DepartmentCostPoint, ...]
    start_date: str
    end_date: str
    currency: str = "USD"


class IDepartmentCostService(ABC):
    """部门成本服务接口 — 查询部门级别的 AWS 成本。"""

    @abstractmethod
    async def get_department_cost_report(
        self, department_id: int, start_date: str, end_date: str,
    ) -> DepartmentCostReport:
        """获取部门成本报告。

        Args:
            department_id: 部门 ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            部门成本报告

        Raises:
            DepartmentNotFoundError: 部门不存在
            BudgetNotFoundError: 该部门当月预算不存在
        """
