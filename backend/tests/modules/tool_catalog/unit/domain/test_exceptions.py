"""Tool Catalog 领域异常单元测试。"""

import pytest

from src.modules.tool_catalog.domain.exceptions import (
    ToolNameDuplicateError,
    ToolNotFoundError,
)
from src.shared.domain.exceptions import DuplicateEntityError, EntityNotFoundError


@pytest.mark.unit
class TestToolNotFoundError:
    def test_message_contains_id(self) -> None:
        error = ToolNotFoundError(tool_id=42)
        assert "42" in error.message
        assert "Tool" in error.message

    def test_inherits_entity_not_found_error(self) -> None:
        assert issubclass(ToolNotFoundError, EntityNotFoundError)

    def test_error_code(self) -> None:
        error = ToolNotFoundError(tool_id=1)
        assert error.code == "NOT_FOUND_TOOL"


@pytest.mark.unit
class TestToolNameDuplicateError:
    def test_message_contains_name(self) -> None:
        error = ToolNameDuplicateError(name="My Tool", creator_id=1)
        assert "My Tool" in error.message
        assert "Tool" in error.message

    def test_inherits_duplicate_entity_error(self) -> None:
        assert issubclass(ToolNameDuplicateError, DuplicateEntityError)

    def test_error_code(self) -> None:
        error = ToolNameDuplicateError(name="My Tool", creator_id=1)
        assert error.code == "DUPLICATE_TOOL"

    def test_creator_id_stored(self) -> None:
        error = ToolNameDuplicateError(name="My Tool", creator_id=42)
        assert error.creator_id == 42
