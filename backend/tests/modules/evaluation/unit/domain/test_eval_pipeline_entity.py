"""EvalPipeline 实体单元测试。"""

import pytest

from src.modules.evaluation.domain.entities.eval_pipeline import EvalPipeline
from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus
from src.shared.domain.exceptions import InvalidStateTransitionError


def make_pipeline(
    *,
    suite_id: int = 1,
    agent_id: int = 1,
    trigger: str = "manual",
    model_ids: list[str] | None = None,
) -> EvalPipeline:
    return EvalPipeline(
        suite_id=suite_id,
        agent_id=agent_id,
        trigger=trigger,
        model_ids=model_ids or ["us.anthropic.claude-haiku-4-20250514-v1:0"],
    )


class TestEvalPipelineEntity:
    def test_default_status_is_scheduled(self) -> None:
        pipeline = make_pipeline()
        assert pipeline.status == PipelineStatus.SCHEDULED

    def test_start_transitions_scheduled_to_running(self) -> None:
        pipeline = make_pipeline()
        pipeline.start()
        assert pipeline.status == PipelineStatus.RUNNING
        assert pipeline.started_at is not None

    def test_start_fails_if_not_scheduled(self) -> None:
        pipeline = make_pipeline()
        pipeline.start()
        with pytest.raises(InvalidStateTransitionError):
            pipeline.start()

    def test_complete_transitions_running_to_completed(self) -> None:
        pipeline = make_pipeline()
        pipeline.start()
        pipeline.complete(bedrock_job_id="job-123", score_summary={"accuracy": 0.9})
        assert pipeline.status == PipelineStatus.COMPLETED
        assert pipeline.bedrock_job_id == "job-123"
        assert pipeline.score_summary == {"accuracy": 0.9}

    def test_complete_fails_if_not_running(self) -> None:
        pipeline = make_pipeline()
        with pytest.raises(InvalidStateTransitionError):
            pipeline.complete(bedrock_job_id="job-x", score_summary={})

    def test_fail_transitions_running_to_failed(self) -> None:
        pipeline = make_pipeline()
        pipeline.start()
        pipeline.fail(error="timeout")
        assert pipeline.status == PipelineStatus.FAILED
        assert pipeline.error_message == "timeout"

    def test_empty_model_ids_raises_validation_error(self) -> None:
        with pytest.raises(Exception):  # ValueError or ValidationError
            EvalPipeline(suite_id=1, agent_id=1, trigger="manual", model_ids=[])
