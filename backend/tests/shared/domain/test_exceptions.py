"""DomainError 异常体系测试。"""

import pytest

from src.shared.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    ValidationError,
)


@pytest.mark.unit
class TestDomainError:
    def test_domain_error_is_exception(self):
        error = DomainError("something went wrong")
        assert isinstance(error, Exception)

    def test_domain_error_message(self):
        error = DomainError("something went wrong")
        assert str(error) == "something went wrong"
        assert error.message == "something went wrong"

    def test_domain_error_default_message(self):
        error = DomainError()
        assert str(error) == "领域错误"

    def test_domain_error_default_code(self):
        error = DomainError()
        assert error.code == "DOMAIN_ERROR"

    def test_domain_error_custom_code(self):
        error = DomainError("custom", code="CUSTOM_CODE")
        assert error.code == "CUSTOM_CODE"


@pytest.mark.unit
class TestEntityNotFoundError:
    def test_inherits_domain_error(self):
        error = EntityNotFoundError(entity_type="User", entity_id=42)
        assert isinstance(error, DomainError)

    def test_message_format(self):
        error = EntityNotFoundError(entity_type="User", entity_id=42)
        assert "User" in str(error)
        assert "42" in str(error)

    def test_code_format(self):
        error = EntityNotFoundError(entity_type="User", entity_id=42)
        assert error.code == "NOT_FOUND_USER"

    def test_attributes(self):
        error = EntityNotFoundError(entity_type="User", entity_id=42)
        assert error.entity_type == "User"
        assert error.entity_id == 42


@pytest.mark.unit
class TestDuplicateEntityError:
    def test_inherits_domain_error(self):
        error = DuplicateEntityError(entity_type="User", field="email", value="a@b.com")
        assert isinstance(error, DomainError)

    def test_message_format(self):
        error = DuplicateEntityError(entity_type="User", field="email", value="a@b.com")
        assert "User" in str(error)
        assert "email" in str(error)

    def test_code_format(self):
        error = DuplicateEntityError(entity_type="User", field="email", value="a@b.com")
        assert error.code == "DUPLICATE_USER"

    def test_attributes(self):
        error = DuplicateEntityError(entity_type="User", field="email", value="a@b.com")
        assert error.entity_type == "User"
        assert error.field == "email"
        assert error.value == "a@b.com"


@pytest.mark.unit
class TestInvalidStateTransitionError:
    def test_inherits_domain_error(self):
        error = InvalidStateTransitionError(
            entity_type="Task", current_state="completed", target_state="draft",
        )
        assert isinstance(error, DomainError)

    def test_message_format(self):
        error = InvalidStateTransitionError(
            entity_type="Task", current_state="completed", target_state="draft",
        )
        assert "Task" in str(error)
        assert "completed" in str(error)
        assert "draft" in str(error)

    def test_code_format(self):
        error = InvalidStateTransitionError(
            entity_type="Task", current_state="completed", target_state="draft",
        )
        assert error.code == "INVALID_STATE_TASK"

    def test_attributes(self):
        error = InvalidStateTransitionError(
            entity_type="Task", current_state="completed", target_state="draft",
        )
        assert error.entity_type == "Task"
        assert error.current_state == "completed"
        assert error.target_state == "draft"


@pytest.mark.unit
class TestValidationError:
    def test_inherits_domain_error(self):
        error = ValidationError(message="名称不能为空")
        assert isinstance(error, DomainError)

    def test_message(self):
        error = ValidationError(message="名称不能为空")
        assert str(error) == "名称不能为空"

    def test_code(self):
        error = ValidationError(message="名称不能为空")
        assert error.code == "INVALID_INPUT"

    def test_with_field(self):
        error = ValidationError(message="不能为空", field="name")
        assert error.field == "name"

    def test_field_default_none(self):
        error = ValidationError(message="通用错误")
        assert error.field is None


@pytest.mark.unit
class TestResourceQuotaExceededError:
    def test_inherits_domain_error(self):
        error = ResourceQuotaExceededError(
            resource_type="Agent", quota=10, requested=11,
        )
        assert isinstance(error, DomainError)

    def test_message_format(self):
        error = ResourceQuotaExceededError(
            resource_type="Agent", quota=10, requested=11,
        )
        assert "Agent" in str(error)

    def test_code_format(self):
        error = ResourceQuotaExceededError(
            resource_type="Agent", quota=10, requested=11,
        )
        assert error.code == "QUOTA_EXCEEDED_AGENT"

    def test_attributes(self):
        error = ResourceQuotaExceededError(
            resource_type="Agent", quota=10, requested=11,
        )
        assert error.resource_type == "Agent"
        assert error.quota == 10
        assert error.requested == 11


@pytest.mark.unit
class TestExceptionHierarchy:
    """验证所有异常都是 DomainError 的子类。"""

    @pytest.mark.parametrize(
        "exc_class",
        [
            EntityNotFoundError,
            DuplicateEntityError,
            InvalidStateTransitionError,
            ValidationError,
            ResourceQuotaExceededError,
        ],
    )
    def test_all_exceptions_inherit_domain_error(self, exc_class):
        assert issubclass(exc_class, DomainError)
