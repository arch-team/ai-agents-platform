"""测试用例领域实体。"""

from pydantic import Field

from src.shared.domain.base_entity import PydanticEntity


class TestCase(PydanticEntity):
    """测试用例实体，定义单个评估场景。"""

    suite_id: int
    input_prompt: str = Field(min_length=1, max_length=10000)
    expected_output: str = Field(default="", max_length=10000)
    evaluation_criteria: str = Field(default="", max_length=2000)
    order_index: int = 0
