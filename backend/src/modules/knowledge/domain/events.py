"""knowledge 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class KnowledgeBaseCreatedEvent(DomainEvent):
    """知识库创建事件。"""

    knowledge_base_id: int = 0
    owner_id: int = 0


@dataclass
class KnowledgeBaseActivatedEvent(DomainEvent):
    """知识库激活事件。"""

    knowledge_base_id: int = 0


@dataclass
class KnowledgeBaseSyncStartedEvent(DomainEvent):
    """知识库同步开始事件。"""

    knowledge_base_id: int = 0


@dataclass
class KnowledgeBaseDeletedEvent(DomainEvent):
    """知识库删除事件。"""

    knowledge_base_id: int = 0
    owner_id: int = 0


@dataclass
class DocumentUploadedEvent(DomainEvent):
    """文档上传事件。"""

    document_id: int = 0
    knowledge_base_id: int = 0
    filename: str = ""


@dataclass
class DocumentIndexedEvent(DomainEvent):
    """文档索引完成事件。"""

    document_id: int = 0
    knowledge_base_id: int = 0
    chunk_count: int = 0
