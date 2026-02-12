"""Evaluation API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class TestSuiteResponse(BaseModel):
    """测试集响应。"""

    id: int
    name: str
    description: str
    agent_id: int
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


class TestSuiteListResponse(BaseModel):
    """测试集列表响应。"""

    items: list[TestSuiteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestCaseResponse(BaseModel):
    """测试用例响应。"""

    id: int
    suite_id: int
    input_prompt: str
    expected_output: str
    evaluation_criteria: str
    order_index: int
    created_at: datetime
    updated_at: datetime


class TestCaseListResponse(BaseModel):
    """测试用例列表响应。"""

    items: list[TestCaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EvaluationRunResponse(BaseModel):
    """评估运行响应。"""

    id: int
    suite_id: int
    agent_id: int
    user_id: int
    status: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    score: float
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EvaluationRunListResponse(BaseModel):
    """评估运行列表响应。"""

    items: list[EvaluationRunResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EvaluationResultResponse(BaseModel):
    """评估结果响应。"""

    id: int
    run_id: int
    case_id: int
    actual_output: str
    score: float
    passed: bool
    error_message: str
    created_at: datetime
    updated_at: datetime


class EvaluationResultListResponse(BaseModel):
    """评估结果列表响应。"""

    items: list[EvaluationResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
