"""评估模块。"""

from src.modules.evaluation.api.endpoints import router
from src.modules.evaluation.application.services.evaluation_service import EvaluationService
from src.modules.evaluation.application.services.test_suite_service import TestSuiteService
from src.modules.evaluation.domain.entities.evaluation_result import EvaluationResult
from src.modules.evaluation.domain.entities.evaluation_run import EvaluationRun
from src.modules.evaluation.domain.entities.test_case import TestCase
from src.modules.evaluation.domain.entities.test_suite import TestSuite
from src.modules.evaluation.domain.events import (
    EvaluationRunCompletedEvent,
    TestSuiteActivatedEvent,
    TestSuiteArchivedEvent,
    TestSuiteCreatedEvent,
)


__all__ = [
    "EvaluationResult",
    "EvaluationRun",
    "EvaluationRunCompletedEvent",
    "EvaluationService",
    "TestCase",
    "TestSuite",
    "TestSuiteActivatedEvent",
    "TestSuiteArchivedEvent",
    "TestSuiteCreatedEvent",
    "TestSuiteService",
    "router",
]
