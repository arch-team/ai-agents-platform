"""Memory API 请求/响应模型。"""

from pydantic import BaseModel, Field


class MemoryItemResponse(BaseModel):
    """Memory 条目响应。"""

    memory_id: str
    content: str
    topic: str
    relevance_score: float = 0.0


class SaveMemoryRequest(BaseModel):
    """保存 Memory 请求。"""

    content: str = Field(min_length=1, max_length=10000)
    topic: str = Field(min_length=1, max_length=200)


class SaveMemoryResponse(BaseModel):
    """保存 Memory 响应。"""

    memory_id: str


class SearchMemoryRequest(BaseModel):
    """搜索 Memory 请求。"""

    query: str = Field(min_length=1, max_length=1000)
    max_results: int = Field(default=5, ge=1, le=50)
