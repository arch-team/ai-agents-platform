"""Evaluation API 端点。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.evaluation.api.dependencies import get_evaluation_service, get_test_suite_service
from src.modules.evaluation.api.schemas.requests import (
    CreateEvaluationRunRequest,
    CreateTestCaseRequest,
    CreateTestSuiteRequest,
    UpdateTestSuiteRequest,
)
from src.modules.evaluation.api.schemas.responses import (
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
from src.modules.evaluation.application.services.evaluation_service import EvaluationService
from src.modules.evaluation.application.services.test_suite_service import TestSuiteService
from src.shared.api.schemas import calc_total_pages


router = APIRouter(tags=["evaluation"])

SuiteServiceDep = Annotated[TestSuiteService, Depends(get_test_suite_service)]
EvalServiceDep = Annotated[EvaluationService, Depends(get_evaluation_service)]
CurrentUserDep = Annotated[UserDTO, Depends(get_current_user)]


# -- 响应转换 --

def _to_suite_response(dto: TestSuiteDTO) -> TestSuiteResponse:
    return TestSuiteResponse(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        agent_id=dto.agent_id,
        status=dto.status,
        owner_id=dto.owner_id,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _to_case_response(dto: TestCaseDTO) -> TestCaseResponse:
    return TestCaseResponse(
        id=dto.id,
        suite_id=dto.suite_id,
        input_prompt=dto.input_prompt,
        expected_output=dto.expected_output,
        evaluation_criteria=dto.evaluation_criteria,
        order_index=dto.order_index,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _to_run_response(dto: EvaluationRunDTO) -> EvaluationRunResponse:
    return EvaluationRunResponse(
        id=dto.id,
        suite_id=dto.suite_id,
        agent_id=dto.agent_id,
        user_id=dto.user_id,
        status=dto.status,
        total_cases=dto.total_cases,
        passed_cases=dto.passed_cases,
        failed_cases=dto.failed_cases,
        score=dto.score,
        started_at=dto.started_at,
        completed_at=dto.completed_at,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


def _to_result_response(dto: EvaluationResultDTO) -> EvaluationResultResponse:
    return EvaluationResultResponse(
        id=dto.id,
        run_id=dto.run_id,
        case_id=dto.case_id,
        actual_output=dto.actual_output,
        score=dto.score,
        passed=dto.passed,
        error_message=dto.error_message,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


# -- 测试集端点 --

@router.post(
    "/api/v1/test-suites",
    response_model=TestSuiteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_test_suite(
    request: CreateTestSuiteRequest,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """创建测试集。"""
    dto = CreateTestSuiteDTO(
        name=request.name,
        description=request.description,
        agent_id=request.agent_id,
    )
    result = await service.create_suite(dto, current_user.id)
    return _to_suite_response(result)


@router.get("/api/v1/test-suites", response_model=TestSuiteListResponse)
async def list_test_suites(
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
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


@router.get("/api/v1/test-suites/{suite_id}", response_model=TestSuiteResponse)
async def get_test_suite(
    suite_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """获取测试集详情。"""
    result = await service.get_suite(suite_id, current_user.id)
    return _to_suite_response(result)


@router.put("/api/v1/test-suites/{suite_id}", response_model=TestSuiteResponse)
async def update_test_suite(
    suite_id: int,
    request: UpdateTestSuiteRequest,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """更新测试集。"""
    dto = UpdateTestSuiteDTO(
        name=request.name,
        description=request.description,
    )
    result = await service.update_suite(suite_id, dto, current_user.id)
    return _to_suite_response(result)


@router.delete(
    "/api/v1/test-suites/{suite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_test_suite(
    suite_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """删除测试集（仅 DRAFT 状态）。"""
    await service.delete_suite(suite_id, current_user.id)


@router.post(
    "/api/v1/test-suites/{suite_id}/activate",
    response_model=TestSuiteResponse,
)
async def activate_test_suite(
    suite_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """激活测试集。"""
    result = await service.activate_suite(suite_id, current_user.id)
    return _to_suite_response(result)


@router.post(
    "/api/v1/test-suites/{suite_id}/archive",
    response_model=TestSuiteResponse,
)
async def archive_test_suite(
    suite_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestSuiteResponse:
    """归档测试集。"""
    result = await service.archive_suite(suite_id, current_user.id)
    return _to_suite_response(result)


# -- 测试用例端点 --

@router.post(
    "/api/v1/test-suites/{suite_id}/cases",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_test_case(
    suite_id: int,
    request: CreateTestCaseRequest,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> TestCaseResponse:
    """添加测试用例到测试集。"""
    dto = CreateTestCaseDTO(
        input_prompt=request.input_prompt,
        expected_output=request.expected_output,
        evaluation_criteria=request.evaluation_criteria,
        order_index=request.order_index,
    )
    result = await service.add_test_case(suite_id, dto, current_user.id)
    return _to_case_response(result)


@router.get(
    "/api/v1/test-suites/{suite_id}/cases",
    response_model=TestCaseListResponse,
)
async def list_test_cases(
    suite_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TestCaseListResponse:
    """列出测试集的测试用例。"""
    paged = await service.list_test_cases(
        suite_id, current_user.id, page=page, page_size=page_size,
    )
    return TestCaseListResponse(
        items=[_to_case_response(c) for c in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, paged.page_size),
    )


@router.delete(
    "/api/v1/test-suites/{suite_id}/cases/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_test_case(
    suite_id: int,
    case_id: int,
    service: SuiteServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """删除测试用例。"""
    await service.delete_test_case(suite_id, case_id, current_user.id)


# -- 评估运行端点 --

@router.post(
    "/api/v1/evaluation-runs",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation_run(
    request: CreateEvaluationRunRequest,
    service: EvalServiceDep,
    current_user: CurrentUserDep,
) -> EvaluationRunResponse:
    """执行评估运行。"""
    dto = CreateEvaluationRunDTO(suite_id=request.suite_id)
    result = await service.run_evaluation(dto, current_user.id)
    return _to_run_response(result)


@router.get("/api/v1/evaluation-runs", response_model=EvaluationRunListResponse)
async def list_evaluation_runs(
    service: EvalServiceDep,
    current_user: CurrentUserDep,
    suite_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> EvaluationRunListResponse:
    """列出评估运行。"""
    paged = await service.list_runs(
        current_user.id, suite_id=suite_id, page=page, page_size=page_size,
    )
    return EvaluationRunListResponse(
        items=[_to_run_response(r) for r in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, paged.page_size),
    )


@router.get("/api/v1/evaluation-runs/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation_run(
    run_id: int,
    service: EvalServiceDep,
) -> EvaluationRunResponse:
    """获取评估运行详情。"""
    result = await service.get_run(run_id)
    return _to_run_response(result)


@router.get(
    "/api/v1/evaluation-runs/{run_id}/results",
    response_model=EvaluationResultListResponse,
)
async def get_evaluation_results(
    run_id: int,
    service: EvalServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> EvaluationResultListResponse:
    """获取评估运行的结果列表。"""
    paged = await service.get_results(run_id, page=page, page_size=page_size)
    return EvaluationResultListResponse(
        items=[_to_result_response(r) for r in paged.items],
        total=paged.total,
        page=paged.page,
        page_size=paged.page_size,
        total_pages=calc_total_pages(paged.total, paged.page_size),
    )
