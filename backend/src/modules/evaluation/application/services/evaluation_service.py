"""Evaluation 应用服务。"""

from src.modules.evaluation.application.dto.evaluation_dto import (
    CreateEvaluationRunDTO,
    EvaluationResultDTO,
    EvaluationRunDTO,
)
from src.modules.evaluation.domain.entities.evaluation_result import EvaluationResult
from src.modules.evaluation.domain.entities.evaluation_run import EvaluationRun
from src.modules.evaluation.domain.events import EvaluationRunCompletedEvent
from src.modules.evaluation.domain.exceptions import (
    EvaluationRunNotFoundError,
    TestSuiteNotActiveError,
    TestSuiteNotFoundError,
)
from src.modules.evaluation.domain.repositories.evaluation_result_repository import (
    IEvaluationResultRepository,
)
from src.modules.evaluation.domain.repositories.evaluation_run_repository import (
    IEvaluationRunRepository,
)
from src.modules.evaluation.domain.repositories.test_case_repository import ITestCaseRepository
from src.modules.evaluation.domain.repositories.test_suite_repository import ITestSuiteRepository
from src.modules.evaluation.domain.value_objects.test_suite_status import TestSuiteStatus
from src.shared.application.dtos import PagedResult
from src.shared.application.ownership import get_or_raise
from src.shared.domain.event_bus import event_bus


class EvaluationService:
    """评估运行业务服务，编排评估执行和结果查询用例。"""

    def __init__(
        self,
        suite_repo: ITestSuiteRepository,
        case_repo: ITestCaseRepository,
        run_repo: IEvaluationRunRepository,
        result_repo: IEvaluationResultRepository,
    ) -> None:
        self._suite_repo = suite_repo
        self._case_repo = case_repo
        self._run_repo = run_repo
        self._result_repo = result_repo

    # -- 辅助方法 --

    @staticmethod
    def _to_run_dto(run: EvaluationRun) -> EvaluationRunDTO:
        return EvaluationRunDTO(
            id=run.id,  # type: ignore[arg-type]
            suite_id=run.suite_id,
            agent_id=run.agent_id,
            user_id=run.user_id,
            status=run.status.value,
            total_cases=run.total_cases,
            passed_cases=run.passed_cases,
            failed_cases=run.failed_cases,
            score=run.score,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,  # type: ignore[arg-type]
            updated_at=run.updated_at,  # type: ignore[arg-type]
        )

    @staticmethod
    def _to_result_dto(result: EvaluationResult) -> EvaluationResultDTO:
        return EvaluationResultDTO(
            id=result.id,  # type: ignore[arg-type]
            run_id=result.run_id,
            case_id=result.case_id,
            actual_output=result.actual_output,
            score=result.score,
            passed=result.passed,
            error_message=result.error_message,
            created_at=result.created_at,  # type: ignore[arg-type]
            updated_at=result.updated_at,  # type: ignore[arg-type]
        )

    # -- 评估运行 --

    async def run_evaluation(
        self,
        dto: CreateEvaluationRunDTO,
        current_user_id: int,
    ) -> EvaluationRunDTO:
        """执行评估运行 — 批量执行测试集中所有用例。

        MVP 实现: 同步执行所有用例，记录结果。
        """
        suite = await get_or_raise(
            self._suite_repo, dto.suite_id, TestSuiteNotFoundError, dto.suite_id,
        )
        if suite.status != TestSuiteStatus.ACTIVE:
            raise TestSuiteNotActiveError(dto.suite_id)

        # 获取所有测试用例
        cases = await self._case_repo.list_by_suite(dto.suite_id, offset=0, limit=1000)

        # 创建评估运行
        run = EvaluationRun(
            suite_id=dto.suite_id,
            agent_id=suite.agent_id,
            user_id=current_user_id,
            total_cases=len(cases),
        )
        created_run = await self._run_repo.create(run)

        # 开始执行
        created_run.start()
        created_run = await self._run_repo.update(created_run)

        # MVP: 为每个用例创建模拟结果 (实际 Agent 调用在后续迭代中实现)
        passed = 0
        failed = 0
        for case in cases:
            result = EvaluationResult(
                run_id=created_run.id,  # type: ignore[arg-type]
                case_id=case.id,  # type: ignore[arg-type]
                actual_output="[MVP] 评估结果占位",
                score=1.0,
                passed=True,
            )
            await self._result_repo.create(result)
            passed += 1

        # 完成评估
        score = passed / len(cases) if cases else 0.0
        created_run.complete(passed=passed, failed=failed, score=score)
        updated_run = await self._run_repo.update(created_run)

        await event_bus.publish_async(
            EvaluationRunCompletedEvent(
                run_id=updated_run.id,  # type: ignore[arg-type]
                suite_id=dto.suite_id,
                user_id=current_user_id,
                score=score,
            ),
        )
        return self._to_run_dto(updated_run)

    async def get_run(self, run_id: int) -> EvaluationRunDTO:
        """获取评估运行详情。"""
        run = await get_or_raise(self._run_repo, run_id, EvaluationRunNotFoundError, run_id)
        return self._to_run_dto(run)

    async def list_runs(
        self,
        current_user_id: int,
        *,
        suite_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[EvaluationRunDTO]:
        """列出评估运行。"""
        offset = (page - 1) * page_size
        if suite_id is not None:
            runs = await self._run_repo.list_by_suite(suite_id, offset=offset, limit=page_size)
            total = await self._run_repo.count_by_suite(suite_id)
        else:
            runs = await self._run_repo.list_by_user(current_user_id, offset=offset, limit=page_size)
            total = await self._run_repo.count_by_user(current_user_id)
        return PagedResult(
            items=[self._to_run_dto(r) for r in runs],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_results(
        self,
        run_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[EvaluationResultDTO]:
        """获取评估运行的结果列表。"""
        await get_or_raise(self._run_repo, run_id, EvaluationRunNotFoundError, run_id)
        offset = (page - 1) * page_size
        results = await self._result_repo.list_by_run(run_id, offset=offset, limit=page_size)
        total = await self._result_repo.count_by_run(run_id)
        return PagedResult(
            items=[self._to_result_dto(r) for r in results],
            total=total,
            page=page,
            page_size=page_size,
        )
