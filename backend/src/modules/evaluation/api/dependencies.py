"""Evaluation API 依赖注入。"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.evaluation.application.services.evaluation_service import EvaluationService
from src.modules.evaluation.application.services.test_suite_service import TestSuiteService
from src.modules.evaluation.infrastructure.persistence.repositories.evaluation_result_repository_impl import (
    EvaluationResultRepositoryImpl,
)
from src.modules.evaluation.infrastructure.persistence.repositories.evaluation_run_repository_impl import (
    EvaluationRunRepositoryImpl,
)
from src.modules.evaluation.infrastructure.persistence.repositories.test_case_repository_impl import (
    TestCaseRepositoryImpl,
)
from src.modules.evaluation.infrastructure.persistence.repositories.test_suite_repository_impl import (
    TestSuiteRepositoryImpl,
)
from src.shared.infrastructure.database import get_db


async def get_test_suite_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TestSuiteService:
    """创建 TestSuiteService 实例。"""
    return TestSuiteService(
        suite_repo=TestSuiteRepositoryImpl(session=session),
        case_repo=TestCaseRepositoryImpl(session=session),
    )


async def get_evaluation_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> EvaluationService:
    """创建 EvaluationService 实例。"""
    return EvaluationService(
        suite_repo=TestSuiteRepositoryImpl(session=session),
        case_repo=TestCaseRepositoryImpl(session=session),
        run_repo=EvaluationRunRepositoryImpl(session=session),
        result_repo=EvaluationResultRepositoryImpl(session=session),
    )
