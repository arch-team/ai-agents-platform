"""Tool Catalog 模块领域异常。"""

from src.shared.domain.exceptions import DuplicateEntityError, EntityNotFoundError


class ToolNotFoundError(EntityNotFoundError):
    """Tool 未找到。"""

    def __init__(self, tool_id: int) -> None:
        super().__init__(entity_type="Tool", entity_id=tool_id)


class ToolNameDuplicateError(DuplicateEntityError):
    """Tool 名称重复（同一创建者下）。"""

    def __init__(self, name: str, creator_id: int) -> None:
        self.creator_id = creator_id
        super().__init__(entity_type="Tool", field="name", value=name)
