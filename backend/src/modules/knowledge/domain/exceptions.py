"""knowledge 模块领域异常。"""

from src.shared.domain.exceptions import DomainError


class KnowledgeBaseNotFoundError(DomainError):
    """知识库不存在。"""

    def __init__(self, kb_id: int) -> None:
        super().__init__(message=f"知识库 {kb_id} 不存在", code="KNOWLEDGE_BASE_NOT_FOUND")


class KnowledgeBaseNameDuplicateError(DomainError):
    """知识库名称重复。"""

    def __init__(self, name: str, owner_id: int) -> None:
        super().__init__(
            message=f"用户 {owner_id} 已存在同名知识库: {name}",
            code="KNOWLEDGE_BASE_NAME_DUPLICATE",
        )


class DocumentNotFoundError(DomainError):
    """文档不存在。"""

    def __init__(self, doc_id: int) -> None:
        super().__init__(message=f"文档 {doc_id} 不存在", code="DOCUMENT_NOT_FOUND")
