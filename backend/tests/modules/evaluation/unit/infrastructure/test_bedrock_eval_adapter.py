"""BedrockEvalAdapter 单元测试。"""

import inspect
from unittest.mock import MagicMock, patch

import pytest

import src.modules.evaluation.infrastructure.external.bedrock_eval_adapter as adapter_module
from src.modules.evaluation.application.interfaces.eval_service import EvalJobResult
from src.modules.evaluation.infrastructure.external.bedrock_eval_adapter import BedrockEvalAdapter
from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def adapter(mock_client: MagicMock) -> BedrockEvalAdapter:
    with patch("boto3.client", return_value=mock_client):
        return BedrockEvalAdapter(region="us-east-1")


class TestBedrockEvalAdapter:
    @pytest.mark.asyncio
    async def test_create_eval_job_returns_job_id(self, adapter: BedrockEvalAdapter, mock_client: MagicMock) -> None:
        mock_client.create_model_evaluation_job.return_value = {
            "jobArn": "arn:aws:bedrock:us-east-1:123456789012:evaluation-job/test-job-001",
        }
        result = await adapter.create_eval_job(
            "测试套件",
            [MODEL_CLAUDE_HAIKU_45],
            [{"input": "q", "expected": "a"}],
        )
        assert result == "test-job-001"
        mock_client.create_model_evaluation_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_eval_job_result_completed(self, adapter: BedrockEvalAdapter, mock_client: MagicMock) -> None:
        mock_client.get_model_evaluation_job.return_value = {
            "status": "Completed",
            "evaluationSummary": {"accuracy": 0.85},
        }
        result = await adapter.get_eval_job_result("test-job-001")
        assert isinstance(result, EvalJobResult)
        assert result.status == "Completed"
        assert result.score_summary == {"accuracy": 0.85}

    def test_adapter_is_under_100_lines(self) -> None:
        source = inspect.getsource(adapter_module)
        line_count = len(source.splitlines())
        assert line_count < 100, f"适配器超过 100 行 ({line_count} 行)，违反 SDK-First 原则"
