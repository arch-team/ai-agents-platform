from src.modules.evaluation.domain.value_objects.pipeline_status import PipelineStatus


class TestPipelineStatus:
    def test_all_statuses_are_strings(self) -> None:
        for status in PipelineStatus:
            assert isinstance(status.value, str)

    def test_scheduled_is_initial_status(self) -> None:
        assert PipelineStatus.SCHEDULED.value == "scheduled"

    def test_status_values(self) -> None:
        assert PipelineStatus.SCHEDULED == "scheduled"
        assert PipelineStatus.RUNNING == "running"
        assert PipelineStatus.COMPLETED == "completed"
        assert PipelineStatus.FAILED == "failed"
