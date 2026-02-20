"""Bedrock Evaluation 外部服务接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class EvalJobResult:
    """Bedrock Evaluation Job 结果。"""

    job_id: str
    status: str  # "Completed" | "Failed" | "InProgress"
    score_summary: dict[str, Any]


class IEvalService(ABC):
    """Bedrock Model Evaluation 服务接口（封装层 < 100 行）。"""

    @abstractmethod
    async def create_eval_job(
        self,
        suite_name: str,
        model_ids: list[str],
        test_cases: list[dict[str, str]],
    ) -> str:
        """创建 Bedrock Evaluation Job，返回 job_id。"""
        ...

    @abstractmethod
    async def get_eval_job_result(self, job_id: str) -> EvalJobResult:
        """查询 Evaluation Job 结果。"""
        ...
