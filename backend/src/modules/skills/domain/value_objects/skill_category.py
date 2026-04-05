"""Skill 分类枚举。"""

from enum import StrEnum


class SkillCategory(StrEnum):
    """Skill 业务分类。"""

    CUSTOMER_SERVICE = "customer_service"
    ORDER_MANAGEMENT = "order_management"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_CREATION = "content_creation"
    WORKFLOW_AUTOMATION = "workflow_automation"
    GENERAL = "general"
