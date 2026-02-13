"""按日维度的使用趋势值对象。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DailyUsageTrend:
    """单日使用趋势聚合数据。"""

    date: str
    invocation_count: int
    total_tokens: int
    unique_users: int
