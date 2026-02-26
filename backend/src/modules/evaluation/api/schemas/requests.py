"""Evaluation API 请求模型。"""

from pydantic import BaseModel, Field

from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45


class CreateTestSuiteRequest(BaseModel):
    """创建测试集请求。"""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    agent_id: int = Field(gt=0)


class UpdateTestSuiteRequest(BaseModel):
    """更新测试集请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class CreateTestCaseRequest(BaseModel):
    """创建测试用例请求。"""

    input_prompt: str = Field(min_length=1, max_length=10000)
    expected_output: str = Field(default="", max_length=10000)
    evaluation_criteria: str = Field(default="", max_length=2000)
    order_index: int = Field(default=0, ge=0)


class CreateEvaluationRunRequest(BaseModel):
    """创建评估运行请求。"""

    suite_id: int = Field(gt=0)


class TriggerPipelineRequest(BaseModel):
    """触发 Eval Pipeline 请求。"""

    model_ids: list[str] = [MODEL_CLAUDE_HAIKU_45]
