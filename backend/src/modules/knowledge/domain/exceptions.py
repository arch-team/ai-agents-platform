"""knowledge 模块领域异常。"""

from src.shared.domain.exceptions import DuplicateEntityError, EntityNotFoundError


class KnowledgeBaseNotFoundError(EntityNotFoundError):
    """知识库不存在。"""

    def __init__(self, kb_id: int) -> None:
        super().__init__(entity_type="KnowledgeBase", entity_id=kb_id)


class KnowledgeBaseNameDuplicateError(DuplicateEntityError):
    """知识库名称重复。"""

    def __init__(self, name: str, owner_id: int) -> None:
        self.owner_id = owner_id
        super().__init__(entity_type="KnowledgeBase", field="name", value=name)


class DocumentNotFoundError(EntityNotFoundError):
    """文档不存在。"""

    def __init__(self, doc_id: int) -> None:
        super().__init__(entity_type="Document", entity_id=doc_id)
