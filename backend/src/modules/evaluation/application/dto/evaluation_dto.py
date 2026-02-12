"""Evaluation 相关 DTO。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateTestSuiteDTO:
    """创建测试集请求数据。"""

    name: str
    description: str
    agent_id: int


@dataclass
class UpdateTestSuiteDTO:
    """更新测试集请求数据。"""

    name: str | None = None
    description: str | None = None


@dataclass
class TestSuiteDTO:
    """测试集响应数据。"""

    id: int
    name: str
    description: str
    agent_id: int
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateTestCaseDTO:
    """创建测试用例请求数据。"""

    input_prompt: str
    expected_output: str = ""
    evaluation_criteria: str = ""
    order_index: int = 0


@dataclass
class TestCaseDTO:
    """测试用例响应数据。"""

    id: int
    suite_id: int
    input_prompt: str
    expected_output: str
    evaluation_criteria: str
    order_index: int
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateEvaluationRunDTO:
    """创建评估运行请求数据。"""

    suite_id: int


@dataclass
class EvaluationRunDTO:
    """评估运行响应数据。"""

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


@dataclass
class EvaluationResultDTO:
    """评估结果响应数据。"""

    id: int
    run_id: int
    case_id: int
    actual_output: str
    score: float
    passed: bool
    error_message: str
    created_at: datetime
    updated_at: datetime
