"""审计模块异常单元测试。"""

import pytest

from src.modules.audit.domain.exceptions import AuditError, AuditNotFoundError
from src.shared.domain.exceptions import DomainError, EntityNotFoundError


@pytest.mark.unit
class TestAuditError:
    def test_inherits_domain_error(self) -> None:
        err = AuditError()
        assert isinstance(err, DomainError)
        assert err.message == "审计错误"
        assert err.code == "AUDIT_ERROR"

    def test_custom_message(self) -> None:
        err = AuditError("自定义错误信息")
        assert err.message == "自定义错误信息"


@pytest.mark.unit
class TestAuditNotFoundError:
    def test_inherits_entity_not_found_error(self) -> None:
        err = AuditNotFoundError(42)
        assert isinstance(err, EntityNotFoundError)
        assert err.entity_type == "AuditLog"
        assert err.entity_id == 42
        assert "AuditLog(id=42)" in err.message
