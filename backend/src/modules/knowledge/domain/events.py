"""knowledge 模块领域事件。"""

from dataclasses import dataclass

from src.shared.domain.events import DomainEvent


@dataclass
class _KnowledgeBaseEvent(DomainEvent):
    """知识库事件基类，携带 knowledge_base_id。"""

    knowledge_base_id: int = 0


@dataclass
class KnowledgeBaseCreatedEvent(_KnowledgeBaseEvent):
    """知识库创建事件。"""

    owner_id: int = 0


@dataclass
class KnowledgeBaseActivatedEvent(_KnowledgeBaseEvent):
    """知识库激活事件。"""


@dataclass
class KnowledgeBaseSyncStartedEvent(_KnowledgeBaseEvent):
    """知识库同步开始事件。"""


@dataclass
class KnowledgeBaseDeletedEvent(_KnowledgeBaseEvent):
    """知识库删除事件。"""

    owner_id: int = 0


@dataclass
class _DocumentEvent(DomainEvent):
    """文档事件基类，携带 document_id 和 knowledge_base_id。"""

    document_id: int = 0
    knowledge_base_id: int = 0


@dataclass
class DocumentUploadedEvent(_DocumentEvent):
    """文档上传事件。"""

    filename: str = ""


@dataclass
class DocumentIndexedEvent(_DocumentEvent):
    """文档索引完成事件。"""

    chunk_count: int = 0
