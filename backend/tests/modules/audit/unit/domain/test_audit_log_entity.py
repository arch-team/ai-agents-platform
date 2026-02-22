"""AuditLog 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.audit.domain.entities.audit_log import AuditAction, AuditCategory, AuditLog
from tests.modules.audit.conftest import make_audit_log


@pytest.mark.unit
class TestAuditLogCreation:
    def test_create_audit_log_with_required_fields(self) -> None:
        log = AuditLog(
            actor_id=1,
            actor_name="管理员",
            action=AuditAction.CREATE,
            category=AuditCategory.AGENT_MANAGEMENT,
            resource_type="agent",
            resource_id="42",
            module="agents",
        )
        assert log.actor_id == 1
        assert log.actor_name == "管理员"
        assert log.action == AuditAction.CREATE
        assert log.category == AuditCategory.AGENT_MANAGEMENT
        assert log.resource_type == "agent"
        assert log.resource_id == "42"
        assert log.module == "agents"
        assert log.result == "success"
        assert log.resource_name is None
        assert log.ip_address is None
        assert log.error_message is None
        assert log.details is None

    def test_create_audit_log_with_all_fields(self) -> None:
        log = make_audit_log(
            details={"key": "value", "count": 5},
        )
        assert log.id == 1
        assert log.actor_id == 100
        assert log.details == {"key": "value", "count": 5}
        assert log.ip_address == "127.0.0.1"
        assert log.request_method == "POST"
        assert log.status_code == 201

    def test_create_audit_log_inherits_pydantic_entity(self) -> None:
        log = AuditLog(
            actor_id=1,
            actor_name="用户",
            action=AuditAction.READ,
            category=AuditCategory.SYSTEM,
            resource_type="config",
            resource_id="1",
            module="system",
        )
        assert log.id is None
        assert log.created_at is not None
        assert log.updated_at is not None

    def test_create_audit_log_with_failure_result(self) -> None:
        log = make_audit_log(
            result="failure",
            error_message="权限不足",
            status_code=403,
        )
        assert log.result == "failure"
        assert log.error_message == "权限不足"
        assert log.status_code == 403


@pytest.mark.unit
class TestAuditLogValidation:
    def test_actor_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            AuditLog(
                actor_id=1,
                actor_name="A" * 101,
                action=AuditAction.CREATE,
                category=AuditCategory.SYSTEM,
                resource_type="test",
                resource_id="1",
                module="test",
            )

    def test_resource_type_max_length(self) -> None:
        with pytest.raises(ValidationError):
            AuditLog(
                actor_id=1,
                actor_name="用户",
                action=AuditAction.CREATE,
                category=AuditCategory.SYSTEM,
                resource_type="A" * 51,
                resource_id="1",
                module="test",
            )

    def test_resource_id_max_length(self) -> None:
        with pytest.raises(ValidationError):
            AuditLog(
                actor_id=1,
                actor_name="用户",
                action=AuditAction.CREATE,
                category=AuditCategory.SYSTEM,
                resource_type="test",
                resource_id="A" * 101,
                module="test",
            )

    def test_invalid_action_raises(self) -> None:
        with pytest.raises(ValueError):
            AuditLog(
                actor_id=1,
                actor_name="用户",
                action="invalid_action",  # type: ignore[arg-type]
                category=AuditCategory.SYSTEM,
                resource_type="test",
                resource_id="1",
                module="test",
            )

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(ValueError):
            AuditLog(
                actor_id=1,
                actor_name="用户",
                action=AuditAction.CREATE,
                category="invalid_category",  # type: ignore[arg-type]
                resource_type="test",
                resource_id="1",
                module="test",
            )


@pytest.mark.unit
class TestAuditActionEnum:
    def test_all_actions_defined(self) -> None:
        expected = {
            "create", "read", "update", "delete",
            "login", "logout",
            "activate", "archive",
            "submit", "approve", "reject", "deprecate",
            "execute", "cancel", "export",
        }
        actual = {a.value for a in AuditAction}
        assert actual == expected

    def test_action_string_value(self) -> None:
        assert AuditAction.CREATE == "create"
        assert AuditAction.DELETE == "delete"


@pytest.mark.unit
class TestAuditCategoryEnum:
    def test_all_categories_defined(self) -> None:
        expected = {
            "authentication", "agent_management", "execution",
            "tool_management", "knowledge_management",
            "template_management", "evaluation", "system",
        }
        actual = {c.value for c in AuditCategory}
        assert actual == expected

    def test_category_string_value(self) -> None:
        assert AuditCategory.AUTHENTICATION == "authentication"
        assert AuditCategory.AGENT_MANAGEMENT == "agent_management"
