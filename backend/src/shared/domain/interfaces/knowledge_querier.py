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
    """跨模块知识库查询接口。

    接口定义在 shared/domain/interfaces/，
    实现由 knowledge 模块在 infrastructure 层提供。
    execution 模块的 Application 层依赖此接口进行 RAG 检索。
    """

    @abstractmethod
    async def retrieve(
        self,
        kb_id: int,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """检索知识库。

        Args:
            kb_id: 知识库 ID
            query: 检索查询文本
            top_k: 返回结果数量上限

        Returns:
            检索结果列表，按相关性降序排列。
        """
