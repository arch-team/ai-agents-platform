"""Evaluation API 端点。"""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.evaluation.api.dependencies import (
    get_eval_pipeline_service,
    get_evaluation_service,
    get_test_suite_service,
)
from src.modules.evaluation.api.schemas.requests import (
    CreateEvaluationRunRequest,
    CreateTestCaseRequest,
    CreateTestSuiteRequest,
    TriggerPipelineRequest,
    UpdateTestSuiteRequest,
)
from src.modules.evaluation.api.schemas.responses import (
    EvalPipelineResponse,
    EvaluationResultListResponse,
    EvaluationResultResponse,
    EvaluationRunListResponse,
    EvaluationRunResponse,
    TestCaseListResponse,
    TestCaseResponse,
    TestSuiteListResponse,
    TestSuiteResponse,
)
from src.modules.evaluation.application.dto.evaluation_dto import (
    CreateEvaluationRunDTO,
    CreateTestCaseDTO,
    CreateTestSuiteDTO,
    EvaluationResultDTO,
    EvaluationRunDTO,
    TestCaseDTO,
    TestSuiteDTO,
    UpdateTestSuiteDTO,
)
from src.modules.evaluation.application.dto.pipeline_dto import TriggerPipelineDTO
from src.modules.evaluation.application.services.eval_pipeline_service import EvalPipelineService
from src.modules.evaluation.application.services.evaluation_service import EvaluationService
from src.modules.evaluation.application.services.test_suite_service import TestSuiteService
from src.shared.api.schemas import calc_total_pages


# 使用三个子 router 统一路由前缀, 避免每个端点重复路径
suite_router = APIRouter(prefix="/api/v1/test-suites", tags=["evaluation"])
run_router = APIRouter(prefix="/api/v1/evaluation-runs", tags=["evaluation"])
pipeline_router = APIRouter(prefix="/api/v1/eval-suites", tags=["evaluation"])

SuiteServiceDep = Annotated[TestSuiteService, Depends(get_test_suite_service)]
EvalServiceDep = Annotated[EvaluationService, Depends(get_evaluation_service)]
PipelineServiceDep = Annotated[EvalPipelineService, Depends(get_eval_pipeline_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


# -- 响应转换 --


def _to_suite_response(dto: TestSuiteDTO) -> TestSuiteResponse:
    return TestSuiteResponse(**asdict(dto))


def _to_case_response(dto: TestCaseDTO) -> TestCaseResponse:
    return TestCaseResponse(**asdict(dto))


def _to_run_response(dto: EvaluationRunDTO) -> EvaluationRunResponse:
    return EvaluationRunResponse(**asdict(dto))


def _to_result_response(dto: EvaluationResultDTO) -> EvaluationResultResponse:
    return EvaluationResultResponse(**asdict(dto))


# -- 测试集端点 --


@suite_router.post("", status_code=status.HTTP_201_CREATED)
async def create_test_suite(
    request: CreateTestSuiteRequest,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """创建测试集。"""
    dto = CreateTestSuiteDTO(**request.model_dump())
    result = await service.create_suite(dto, current_user.id)
    return _to_suite_response(result)


@suite_router.get("")
async def list_test_suites(
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TestSuiteListResponse:
    """列出当前用户的测试集。"""
    paged = await service.list_suites(current_user.id, page=page, page_size=page_size)
    return TestSuiteListResponse(
        items=[_to_suite_response(s) for s in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, paged.page_size),
    )


@suite_router.get("/{suite_id}")
async def get_test_suite(suite_id: int, service: SuiteServiceDep, current_user: CurrentUserDep) -> TestSuiteResponse:
    """获取测试集详情。"""
    result = await service.get_suite(suite_id, current_user.id)
    return _to_suite_response(result)


@suite_router.put("/{suite_id}")
async def update_test_suite(
    suite_id: int,
    request: UpdateTestSuiteRequest,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """更新测试集。"""
    dto = UpdateTestSuiteDTO(**request.model_dump())
    result = await service.update_suite(suite_id, dto, current_user.id)
    return _to_suite_response(result)


@suite_router.delete("/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_suite(suite_id: int, service: SuiteServiceDep, current_user: CurrentUserDep) -> None:
    """删除测试集（仅 DRAFT 状态）。"""
    await service.delete_suite(suite_id, current_user.id)


@suite_router.post("/{suite_id}/activate")
async def activate_test_suite(
    suite_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """激活测试集。"""
    result = await service.activate_suite(suite_id, current_user.id)
    return _to_suite_response(result)


@suite_router.post("/{suite_id}/archive")
async def archive_test_suite(
    suite_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """归档测试集。"""
    result = await service.archive_suite(suite_id, current_user.id)
    return _to_suite_response(result)


# -- 测试用例端点 --


@suite_router.post("/{suite_id}/cases", status_code=status.HTTP_201_CREATED)
async def add_test_case(
    suite_id: int,
    request: CreateTestCaseRequest,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestCaseResponse:
    """添加测试用例到测试集。"""
    dto = CreateTestCaseDTO(**request.model_dump())
    result = await service.add_test_case(suite_id, dto, current_user.id)
    return _to_case_response(result)


@suite_router.get("/{suite_id}/cases")
async def list_test_cases(
    suite_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TestCaseListResponse:
    """列出测试集的测试用例。"""
    paged = await service.list_test_cases(suite_id, current_user.id, page=page, page_size=page_size)
    return TestCaseListResponse(
        items=[_to_case_response(c) for c in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, paged.page_size),
    )


@suite_router.delete("/{suite_id}/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    suite_id: int,
    case_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """删除测试用例。"""
    await service.delete_test_case(suite_id, case_id, current_user.id)


# -- 评估运行端点 --


@run_router.post("", status_code=status.HTTP_201_CREATED)
async def create_evaluation_run(
    request: CreateEvaluationRunRequest,
    service: EvalServiceDep,
    current_user: CurrentUserDep,
) -> EvaluationRunResponse:
    """执行评估运行。"""
    dto = CreateEvaluationRunDTO(suite_id=request.suite_id)
    result = await service.run_evaluation(dto, current_user.id)
    return _to_run_response(result)


@run_router.get("")
async def list_evaluation_runs(
    service: EvalServiceDep,
    current_user: CurrentUserDep,
    suite_id: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EvaluationRunListResponse:
    """列出评估运行。"""
    paged = await service.list_runs(current_user.id, suite_id=suite_id, page=page, page_size=page_size)
    return EvaluationRunListResponse(
        items=[_to_run_response(r) for r in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, paged.page_size),
    )


@run_router.get("/{run_id}")
async def get_evaluation_run(
    run_id: int,
    service: EvalServiceDep,
    current_user: CurrentUserDep,
) -> EvaluationRunResponse:
    """获取评估运行详情。"""
    result = await service.get_run(run_id, current_user.id)
    return _to_run_response(result)


@run_router.get("/{run_id}/results")
async def get_evaluation_results(
    run_id: int,
    service: EvalServiceDep,
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EvaluationResultListResponse:
    """获取评估运行的结果列表。"""
    paged = await service.get_results(run_id, current_user.id, page=page, page_size=page_size)
    return EvaluationResultListResponse(
        items=[_to_result_response(r) for r in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, paged.page_size),
    )


# -- Eval Pipeline 端点 --


@pipeline_router.post("/{suite_id}/pipelines", status_code=status.HTTP_201_CREATED)
async def trigger_eval_pipeline(
    suite_id: int,
    body: TriggerPipelineRequest,
    current_user: CurrentUserDep,
    pipeline_service: PipelineServiceDep,
) -> EvalPipelineResponse:
    """触发 Eval Pipeline。"""
    dto = TriggerPipelineDTO(
        suite_id=suite_id,
        agent_id=current_user.id,
        model_ids=body.model_ids,
    )
    result = await pipeline_service.trigger(dto)
    return EvalPipelineResponse(**asdict(result))


@pipeline_router.get("/{suite_id}/pipelines")
async def list_eval_pipelines(
    suite_id: int,
    current_user: CurrentUserDep,  # noqa: ARG001
    pipeline_service: PipelineServiceDep,
) -> list[EvalPipelineResponse]:
    """获取指定 TestSuite 的 Pipeline 列表。"""
    results = await pipeline_service.list_by_suite(suite_id)
    return [EvalPipelineResponse(**asdict(r)) for r in results]


# 合并子 router 供 main.py 注册
router = APIRouter(tags=["evaluation"])
router.include_router(suite_router)
router.include_router(run_router)
router.include_router(pipeline_router)
