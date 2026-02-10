"""文档存储接口 (S3 抽象)。"""

from abc import ABC, abstractmethod


class IDocumentStorage(ABC):
    """文档存储抽象接口 (对接 S3)。"""

    @abstractmethod
    async def upload(self, s3_key: str, content: bytes, *, content_type: str = "application/octet-stream") -> None:
        """上传文档到 S3。"""

    @abstractmethod
    async def delete(self, s3_key: str) -> None:
        """删除 S3 文档。"""

    @abstractmethod
    async def get_presigned_url(self, s3_key: str, *, expires_in: int = 3600) -> str:
        """生成预签名下载 URL。"""
