"""评估结果领域实体。"""

from pydantic import Field

from src.shared.domain.base_entity import PydanticEntity


class EvaluationResult(PydanticEntity):
    """评估结果实体，记录单个测试用例的评估结果。"""

    run_id: int
    case_id: int
    actual_output: str = ""
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    passed: bool = False
    error_message: str = ""
