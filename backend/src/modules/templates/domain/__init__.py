"""模板领域层。"""

from src.modules.templates.domain.entities.template import Template
from src.modules.templates.domain.events import (
    TemplateArchivedEvent,
    TemplateCreatedEvent,
    TemplateInstantiatedEvent,
    TemplatePublishedEvent,
)
from src.modules.templates.domain.exceptions import (
    DuplicateTemplateNameError,
    InvalidTemplateConfigError,
    TemplateError,
    TemplateNotFoundError,
)
from src.modules.templates.domain.repositories.template_repository import (
    ITemplateRepository,
)
from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)
from src.modules.templates.domain.value_objects.template_config import TemplateConfig
from src.modules.templates.domain.value_objects.template_status import TemplateStatus


__all__ = [
    "DuplicateTemplateNameError",
    "ITemplateRepository",
    "InvalidTemplateConfigError",
    "Template",
    "TemplateArchivedEvent",
    "TemplateCategory",
    "TemplateConfig",
    "TemplateCreatedEvent",
    "TemplateError",
    "TemplateInstantiatedEvent",
    "TemplateNotFoundError",
    "TemplatePublishedEvent",
    "TemplateStatus",
]
