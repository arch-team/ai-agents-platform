"""模板分类枚举。"""

from enum import StrEnum


class TemplateCategory(StrEnum):
    """模板分类。"""

    CUSTOMER_SERVICE = "customer_service"
    CODE_ASSISTANT = "code_assistant"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_CREATION = "content_creation"
    RESEARCH = "research"
    WORKFLOW_AUTOMATION = "workflow_automation"
    GENERAL = "general"
