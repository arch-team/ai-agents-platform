"""模板模块。"""

from src.modules.templates.api.endpoints import router
from src.modules.templates.application.services.template_service import TemplateService
from src.modules.templates.domain.entities.template import Template
from src.modules.templates.domain.events import (
    TemplateArchivedEvent,
    TemplateCreatedEvent,
    TemplateInstantiatedEvent,
    TemplatePublishedEvent,
)


__all__ = [
    "Template",
    "TemplateArchivedEvent",
    "TemplateCreatedEvent",
    "TemplateInstantiatedEvent",
    "TemplatePublishedEvent",
    "TemplateService",
    "router",
]
