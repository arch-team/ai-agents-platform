"""templates 模块异常测试。"""

import pytest

from src.modules.templates.domain.exceptions import (
    DuplicateTemplateNameError,
    InvalidTemplateConfigError,
    TemplateError,
    TemplateNotFoundError,
)
from src.shared.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
)


@pytest.mark.unit
class TestTemplateError:
    """TemplateError 基础异常测试。"""

    def test_is_domain_error(self) -> None:
        err = TemplateError("模板错误")
        assert isinstance(err, DomainError)

    def test_message(self) -> None:
        err = TemplateError("自定义模板错误")
        assert err.message == "自定义模板错误"


@pytest.mark.unit
class TestTemplateNotFoundError:
    """TemplateNotFoundError 测试。"""

    def test_message(self) -> None:
        err = TemplateNotFoundError(42)
        assert "42" in str(err.message)
        assert err.code == "NOT_FOUND_TEMPLATE"
        assert isinstance(err, EntityNotFoundError)
        assert isinstance(err, TemplateError)

    def test_entity_attributes(self) -> None:
        err = TemplateNotFoundError(42)
        assert err.entity_type == "Template"
        assert err.entity_id == 42


@pytest.mark.unit
class TestDuplicateTemplateNameError:
    """DuplicateTemplateNameError 测试。"""

    def test_message(self) -> None:
        err = DuplicateTemplateNameError("客服模板")
        assert "客服模板" in str(err.message)
        assert err.code == "DUPLICATE_TEMPLATE"
        assert isinstance(err, DuplicateEntityError)
        assert isinstance(err, TemplateError)


@pytest.mark.unit
class TestInvalidTemplateConfigError:
    """InvalidTemplateConfigError 测试。"""

    def test_message(self) -> None:
        err = InvalidTemplateConfigError("配置不完整")
        assert err.message == "配置不完整"
        assert isinstance(err, TemplateError)
