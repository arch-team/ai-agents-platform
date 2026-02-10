"""知识库外部服务接口 (Bedrock Knowledge Bases 抽象)。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class KBCreateResult:
    """知识库创建结果。"""

    bedrock_kb_id: str
    s3_prefix: str


@dataclass
class KBSyncResult:
    """知识库同步结果。"""

    ingestion_job_id: str
    status: str


@dataclass
class RetrievalChunk:
    """检索结果片段。"""

    content: str
    score: float
    document_id: str = ""
    metadata: dict[str, str] | None = None


class IKnowledgeService(ABC):
    """知识库服务抽象接口 (对接 Bedrock Knowledge Bases)。"""

    @abstractmethod
    async def create_knowledge_base(self, name: str, *, s3_bucket: str, s3_prefix: str) -> KBCreateResult:
        """创建 Bedrock Knowledge Base。"""

    @abstractmethod
    async def delete_knowledge_base(self, bedrock_kb_id: str) -> None:
        """删除 Bedrock Knowledge Base。"""

    @abstractmethod
    async def start_sync(self, bedrock_kb_id: str) -> KBSyncResult:
        """触发数据源同步 (Ingestion Job)。"""

    @abstractmethod
    async def retrieve(
        self,
        bedrock_kb_id: str,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[RetrievalChunk]:
        """语义检索。"""
