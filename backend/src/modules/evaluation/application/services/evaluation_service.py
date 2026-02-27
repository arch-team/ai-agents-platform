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
from src.shared.application.ownership import check_ownership, get_or_raise
from src.shared.domain.event_bus import event_bus


# 单次评估运行最大测试用例数
_MAX_EVALUATION_CASES = 1000


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
        id_, created_at, updated_at = run.require_persisted()
        return EvaluationRunDTO(
            id=id_,
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
            created_at=created_at,
            updated_at=updated_at,
        )

    @staticmethod
    def _to_result_dto(result: EvaluationResult) -> EvaluationResultDTO:
        id_, created_at, updated_at = result.require_persisted()
        return EvaluationResultDTO(
            id=id_,
            run_id=result.run_id,
            case_id=result.case_id,
            actual_output=result.actual_output,
            score=result.score,
            passed=result.passed,
            error_message=result.error_message,
            created_at=created_at,
            updated_at=updated_at,
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
            self._suite_repo,
            dto.suite_id,
            TestSuiteNotFoundError,
            dto.suite_id,
        )
        if suite.status != TestSuiteStatus.ACTIVE:
            raise TestSuiteNotActiveError(dto.suite_id)

        # 获取所有测试用例
        cases = await self._case_repo.list_by_suite(dto.suite_id, offset=0, limit=_MAX_EVALUATION_CASES)

        # 创建评估运行
        run = EvaluationRun(
            suite_id=dto.suite_id,
            agent_id=suite.agent_id,
            user_id=current_user_id,
            total_cases=len(cases),
        )
        created_run = await self._run_repo.create(run)
        if created_run.id is None:
            msg = "EvaluationRun 创建后 ID 不能为空"
            raise ValueError(msg)
        run_id: int = created_run.id

        # 开始执行
        created_run.start()
        created_run = await self._run_repo.update(created_run)

        # MVP: 为每个用例创建模拟结果 (实际 Agent 调用在后续迭代中实现)
        passed = 0
        failed = 0
        for case in cases:
            if case.id is None:
                msg = "TestCase ID 不能为空"
                raise ValueError(msg)
            result = EvaluationResult(
                run_id=run_id,
                case_id=case.id,
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

        if updated_run.id is None:
            msg = "EvaluationRun 更新后 ID 不能为空"
            raise ValueError(msg)
        await event_bus.publish_async(
            EvaluationRunCompletedEvent(
                run_id=updated_run.id,
                suite_id=dto.suite_id,
                user_id=current_user_id,
                score=score,
            ),
        )
        return self._to_run_dto(updated_run)

    async def get_run(self, run_id: int, current_user_id: int) -> EvaluationRunDTO:
        """获取评估运行详情。

        Raises:
            EvaluationRunNotFoundError: 运行不存在
            ForbiddenError: 无权访问此运行
        """
        run = await get_or_raise(self._run_repo, run_id, EvaluationRunNotFoundError, run_id)
        check_ownership(run, current_user_id, owner_field="user_id")
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
        # SQLAlchemy AsyncSession 不支持同一 session 的并发操作, 必须顺序执行
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
        current_user_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PagedResult[EvaluationResultDTO]:
        """获取评估运行的结果列表。

        Raises:
            EvaluationRunNotFoundError: 运行不存在
            ForbiddenError: 无权访问此运行
        """
        run = await get_or_raise(self._run_repo, run_id, EvaluationRunNotFoundError, run_id)
        check_ownership(run, current_user_id, owner_field="user_id")
        offset = (page - 1) * page_size
        # SQLAlchemy AsyncSession 不支持同一 session 的并发操作, 必须顺序执行
        results = await self._result_repo.list_by_run(run_id, offset=offset, limit=page_size)
        total = await self._result_repo.count_by_run(run_id)
        return PagedResult(
            items=[self._to_result_dto(r) for r in results],
            total=total,
            page=page,
            page_size=page_size,
        )
