"""EvalPipelineService 应用服务。"""

import structlog

from src.modules.evaluation.application.dto.pipeline_dto import EvalPipelineDTO, TriggerPipelineDTO
from src.modules.evaluation.application.interfaces.eval_service import IEvalService
from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.exceptions import (
    EvalPipelineNotFoundError,
    PipelineAlreadyRunningError,
    TestSuiteNotFoundError,
)
from src.modules.evaluation.domain.repositories.eval_pipeline_repository import IEvalPipelineRepository
from src.modules.evaluation.domain.repositories.test_case_repository import ITestCaseRepository
from src.modules.evaluation.domain.repositories.test_suite_repository import ITestSuiteRepository
from src.shared.application.ownership import get_or_raise


log = structlog.get_logger(__name__)


class EvalPipelineService:
    """EvalPipeline 业务服务，编排评估流水线触发和查询用例。"""

    def __init__(
        self,
        pipeline_repo: IEvalPipelineRepository,
        suite_repo: ITestSuiteRepository,
        case_repo: ITestCaseRepository,
        eval_service: IEvalService,
    ) -> None:
        self._pipeline_repo = pipeline_repo
        self._suite_repo = suite_repo
        self._case_repo = case_repo
        self._eval_service = eval_service

    @staticmethod
    def _to_dto(pipeline: EvalPipeline) -> EvalPipelineDTO:
        id_, created_at, _ = pipeline.require_persisted()
        return EvalPipelineDTO(
            id=id_,
            suite_id=pipeline.suite_id,
            agent_id=pipeline.agent_id,
            trigger=pipeline.trigger,
            model_ids=pipeline.model_ids,
            status=pipeline.status.value,
            bedrock_job_id=pipeline.bedrock_job_id,
            score_summary=pipeline.score_summary,
            error_message=pipeline.error_message,
            started_at=pipeline.started_at,
            completed_at=pipeline.completed_at,
            created_at=created_at,
        )

    async def trigger(self, dto: TriggerPipelineDTO) -> EvalPipelineDTO:
        """触发评估 Pipeline。

        Raises:
            PipelineAlreadyRunningError: 该 Suite 已有运行中的 Pipeline。
            TestSuiteNotFoundError: 测试集不存在。
        """
        # 1. 防止重复触发
        running = await self._pipeline_repo.find_running_by_suite(dto.suite_id)
        if running is not None:
            raise PipelineAlreadyRunningError

        # 2. 校验 Suite 存在
        suite = await get_or_raise(self._suite_repo, dto.suite_id, TestSuiteNotFoundError, dto.suite_id)

        # 3. 获取测试用例
        cases = await self._case_repo.list_by_suite(dto.suite_id)

        # 4. 创建 Pipeline 实体并持久化
        pipeline = EvalPipeline(
            suite_id=dto.suite_id,
            agent_id=dto.agent_id,
            trigger=dto.trigger,
            model_ids=dto.model_ids,
        )
        pipeline = await self._pipeline_repo.create(pipeline)

        # 5. 启动 Pipeline 状态机
        pipeline.start()

        # 6. 构建 Bedrock 输入格式, 调用外部 Eval 服务
        test_inputs = [{"input": c.input_prompt, "expected": c.expected_output} for c in cases]
        job_id = await self._eval_service.create_eval_job(suite.name, dto.model_ids, test_inputs)

        # 7. 完成 Pipeline 状态机, 更新持久化
        pipeline.complete(bedrock_job_id=job_id, score_summary={})
        pipeline = await self._pipeline_repo.update(pipeline)

        log.info(
            "eval_pipeline_triggered",
            pipeline_id=pipeline.id,
            suite_id=dto.suite_id,
            agent_id=dto.agent_id,
            job_id=job_id,
        )

        return self._to_dto(pipeline)

    async def get(self, *, pipeline_id: int, user_id: int) -> EvalPipelineDTO:  # noqa: ARG002
        """获取 Pipeline 详情。

        Raises:
            EvalPipelineNotFoundError: Pipeline 不存在。
        """
        pipeline = await get_or_raise(self._pipeline_repo, pipeline_id, EvalPipelineNotFoundError, pipeline_id)
        return self._to_dto(pipeline)

    async def list_by_suite(self, suite_id: int) -> list[EvalPipelineDTO]:
        """列出指定 Suite 的 Pipeline 历史。"""
        pipelines = await self._pipeline_repo.list_by_suite(suite_id)
        return [self._to_dto(p) for p in pipelines]
