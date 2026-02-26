"""Eval Pipeline API 端点集成测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.evaluation.api.dependencies import get_eval_pipeline_service
from src.modules.evaluation.application.dto.pipeline_dto import EvalPipelineDTO
from src.presentation.api.main import create_app
from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45


def _now() -> datetime:
    return datetime.now(UTC)


def _make_user(user_id: int = 1) -> UserDTO:
    return UserDTO(id=user_id, email="test@example.com", name="Test", role="developer", is_active=True)


def _make_pipeline_dto(pipeline_id: int = 1) -> EvalPipelineDTO:
    now = _now()
    return EvalPipelineDTO(
        id=pipeline_id,
        suite_id=1,
        agent_id=1,
        trigger="manual",
        model_ids=[MODEL_CLAUDE_HAIKU_45],
        status="completed",
        bedrock_job_id="job-001",
        score_summary={"accuracy": 0.9},
        error_message=None,
        started_at=None,
        completed_at=None,
        created_at=now,
    )


@pytest.fixture
def mock_pipeline_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_pipeline_service: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    app.dependency_overrides[get_eval_pipeline_service] = lambda: mock_pipeline_service
    yield TestClient(app)  # type: ignore[misc]
    app.dependency_overrides.clear()


@pytest.mark.integration
class TestTriggerEvalPipelineEndpoint:
    """POST /api/v1/eval-suites/{suite_id}/pipelines 测试。"""

    def test_post_trigger_returns_201(self, client: TestClient, mock_pipeline_service: AsyncMock) -> None:
        mock_pipeline_service.trigger.return_value = _make_pipeline_dto()
        response = client.post(
            "/api/v1/eval-suites/1/pipelines",
            json={"model_ids": [MODEL_CLAUDE_HAIKU_45]},
        )
        assert response.status_code == 201
        assert response.json()["id"] == 1

    def test_post_trigger_default_model_ids(self, client: TestClient, mock_pipeline_service: AsyncMock) -> None:
        mock_pipeline_service.trigger.return_value = _make_pipeline_dto()
        response = client.post("/api/v1/eval-suites/1/pipelines", json={})
        assert response.status_code == 201

    def test_post_trigger_returns_pipeline_fields(self, client: TestClient, mock_pipeline_service: AsyncMock) -> None:
        mock_pipeline_service.trigger.return_value = _make_pipeline_dto(pipeline_id=42)
        response = client.post(
            "/api/v1/eval-suites/1/pipelines",
            json={"model_ids": ["haiku-id"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 42
        assert data["suite_id"] == 1
        assert data["status"] == "completed"
        assert data["bedrock_job_id"] == "job-001"


@pytest.mark.integration
class TestListEvalPipelinesEndpoint:
    """GET /api/v1/eval-suites/{suite_id}/pipelines 测试。"""

    def test_get_list_returns_200(self, client: TestClient, mock_pipeline_service: AsyncMock) -> None:
        mock_pipeline_service.list_by_suite.return_value = [_make_pipeline_dto()]
        response = client.get("/api/v1/eval-suites/1/pipelines")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_list_returns_empty(self, client: TestClient, mock_pipeline_service: AsyncMock) -> None:
        mock_pipeline_service.list_by_suite.return_value = []
        response = client.get("/api/v1/eval-suites/1/pipelines")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_list_passes_suite_id(self, client: TestClient, mock_pipeline_service: AsyncMock) -> None:
        mock_pipeline_service.list_by_suite.return_value = []
        client.get("/api/v1/eval-suites/99/pipelines")
        mock_pipeline_service.list_by_suite.assert_called_once_with(99)
