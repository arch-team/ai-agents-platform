"""Knowledge API 请求模型。"""

from pydantic import BaseModel, Field


class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库请求。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    agent_id: int | None = None


class UpdateKnowledgeBaseRequest(BaseModel):
    """更新知识库请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    agent_id: int | None = None


class QueryRequest(BaseModel):
    """RAG 检索请求。"""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
