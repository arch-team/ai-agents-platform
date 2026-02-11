"""templates 模块领域异常。"""

from src.shared.domain.exceptions import DomainError, DuplicateEntityError, EntityNotFoundError


class TemplateError(DomainError):
    """模板模块基础异常。"""


class TemplateNotFoundError(TemplateError, EntityNotFoundError):
    """模板不存在。"""

    def __init__(self, template_id: int) -> None:
        EntityNotFoundError.__init__(self, entity_type="Template", entity_id=template_id)


class DuplicateTemplateNameError(TemplateError, DuplicateEntityError):
    """模板名称重复。"""

    def __init__(self, name: str) -> None:
        DuplicateEntityError.__init__(self, entity_type="Template", field="name", value=name)


class InvalidTemplateConfigError(TemplateError):
    """模板配置无效。"""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="INVALID_TEMPLATE_CONFIG")
