"""成本明细值对象。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CostBreakdown:
    """Token 成本明细 — 不可变值对象。"""

    tokens_input: int
    tokens_output: int
    input_cost: float
    output_cost: float
    total_cost: float
    model_id: str
