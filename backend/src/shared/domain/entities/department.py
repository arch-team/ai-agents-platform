"""部门实体 — 多租户隔离的基础维度。"""

from src.shared.domain.base_entity import PydanticEntity


class Department(PydanticEntity):
    """部门实体，用于资源隔离和成本归因。"""

    name: str
    code: str  # 部门编码 (唯一标识, 如 "engineering", "marketing")
    description: str = ""
    is_active: bool = True
