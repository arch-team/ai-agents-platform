"""Knowledge 相关 DTO。"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CreateKnowledgeBaseDTO:
    """创建知识库请求数据。"""

    name: str
    description: str = ""
    agent_id: int | None = None


@dataclass
class UpdateKnowledgeBaseDTO:
    """更新知识库请求数据。"""

    name: str | None = None
    description: str | None = None
    agent_id: int | None = None


@dataclass
class KnowledgeBaseDTO:
    """知识库响应数据。"""

    id: int
    name: str
    description: str
    status: str
    owner_id: int
    agent_id: int | None
    bedrock_kb_id: str
    s3_prefix: str
    created_at: datetime
    updated_at: datetime


@dataclass
class PagedKnowledgeBaseDTO:
    """知识库分页响应数据。"""

    items: list[KnowledgeBaseDTO]
    total: int
    page: int
    page_size: int


@dataclass
class DocumentDTO:
    """文档响应数据。"""

    id: int
    knowledge_base_id: int
    filename: str
    s3_key: str
    file_size: int
    status: str
    content_type: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class UploadDocumentDTO:
    """上传文档请求数据。"""

    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class QueryRequestDTO:
    """RAG 检索请求数据。"""

    query: str
    top_k: int = 5


@dataclass
class QueryResultDTO:
    """RAG 检索结果。"""

    content: str
    score: float
    document_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class QueryResponseDTO:
    """RAG 检索响应数据。"""

    results: list[QueryResultDTO]
    query: str
    knowledge_base_id: int
