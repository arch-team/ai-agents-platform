"""使用量聚合统计值对象。"""

from typing import NamedTuple


class AggregatedStats(NamedTuple):
    """使用量聚合统计 — 不可变值对象。"""

    total_tokens: int
    total_cost: float
    conversation_count: int
    record_count: int
