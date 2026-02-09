"""ToolStatus 枚举单元测试。"""

import pytest

from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus


@pytest.mark.unit
class TestToolStatus:
    def test_draft_value(self) -> None:
        assert ToolStatus.DRAFT == "draft"

    def test_pending_review_value(self) -> None:
        assert ToolStatus.PENDING_REVIEW == "pending_review"

    def test_approved_value(self) -> None:
        assert ToolStatus.APPROVED == "approved"

    def test_rejected_value(self) -> None:
        assert ToolStatus.REJECTED == "rejected"

    def test_deprecated_value(self) -> None:
        assert ToolStatus.DEPRECATED == "deprecated"

    def test_is_str_enum(self) -> None:
        assert isinstance(ToolStatus.DRAFT, str)

    def test_all_members(self) -> None:
        members = {s.value for s in ToolStatus}
        assert members == {
            "draft",
            "pending_review",
            "approved",
            "rejected",
            "deprecated",
        }
