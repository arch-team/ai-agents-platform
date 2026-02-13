"""Knowledge API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseResponse(BaseModel):
    """知识库响应。"""

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


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应。"""

    items: list[KnowledgeBaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentResponse(BaseModel):
    """文档响应。"""

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


class DocumentListResponse(BaseModel):
    """文档列表响应。"""

    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class QueryResultResponse(BaseModel):
    """检索结果项。"""

    content: str
    score: float
    document_id: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    """检索响应。"""

    results: list[QueryResultResponse]
    query: str
    knowledge_base_id: int
