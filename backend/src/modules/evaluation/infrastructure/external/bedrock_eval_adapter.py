"""Bedrock Model Evaluation 适配器。

SDK-First 薄封装层：直接委托 boto3 Bedrock 客户端，
仅做参数映射 + ARN 解析 + 异常转换。封装层 < 100 行。
"""

import asyncio

import boto3
import structlog
from botocore.exceptions import BotoCoreError, ClientError

from src.modules.evaluation.application.interfaces.eval_service import EvalJobResult, IEvalService
from src.shared.domain.exceptions import DomainError


log = structlog.get_logger(__name__)


class BedrockEvalAdapter(IEvalService):
    """Bedrock Model Evaluation 服务适配器（SDK-First，薄封装）。"""

    def __init__(self, region: str = "us-east-1", role_arn: str = "") -> None:
        self._client = boto3.client("bedrock", region_name=region)
        self._role_arn = role_arn

    async def create_eval_job(
        self,
        suite_name: str,
        model_ids: list[str],
        test_cases: list[dict[str, str]],
    ) -> str:  # — MVP: 当前版本不传入自定义数据集
        """创建 Bedrock Evaluation Job，返回 job_id。

        Raises:
            DomainError: Bedrock API 调用失败
        """
        try:
            response = await asyncio.to_thread(
                self._client.create_model_evaluation_job,
                jobName=f"eval-{suite_name[:40].replace(' ', '-')}",
                # TODO(human): 实现 roleArn 赋值逻辑
                roleArn="",
                evaluatorModelConfig={
                    "bedrockEvaluatorModels": [{"modelIdentifier": m} for m in model_ids],
                },
                inferenceConfig={
                    "models": [{"bedrockModel": {"modelIdentifier": model_ids[0]}}],
                },
            )
        except (ClientError, BotoCoreError) as e:
            log.exception("bedrock_create_eval_job_failed", suite_name=suite_name)
            raise DomainError(message="创建 Evaluation Job 失败", code="EVAL_CREATE_FAILED") from e

        job_arn: str = response["jobArn"]
        job_id = job_arn.rsplit("/", 1)[-1]
        log.info("bedrock_eval_job_created", job_id=job_id, suite_name=suite_name)
        return job_id

    async def get_eval_job_result(self, job_id: str) -> EvalJobResult:
        """查询 Evaluation Job 结果。

        Raises:
            DomainError: Bedrock API 调用失败
        """
        try:
            response = await asyncio.to_thread(
                self._client.get_model_evaluation_job,
                jobIdentifier=job_id,
            )
        except (ClientError, BotoCoreError) as e:
            log.exception("bedrock_get_eval_job_failed", job_id=job_id)
            raise DomainError(message="查询 Evaluation Job 失败", code="EVAL_GET_FAILED") from e

        return EvalJobResult(
            job_id=job_id,
            status=response["status"],
            score_summary=response.get("evaluationSummary", {}),
        )
