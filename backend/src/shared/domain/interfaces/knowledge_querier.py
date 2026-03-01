"""跨模块知识库查询接口。

execution 模块依赖此接口进行 RAG 检索，
避免直接导入 knowledge 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalResult:
    """知识库检索结果。"""

    content: str
    score: float


class IKnowledgeQuerier(ABC):
    """跨模块知识库查询接口。"""

    @abstractmethod
    async def retrieve(
        self,
        kb_id: int,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[RetrievalResult]: ...
