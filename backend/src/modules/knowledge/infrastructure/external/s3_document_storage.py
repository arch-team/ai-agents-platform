"""S3 文档存储适配器。"""

import asyncio
from typing import Any

from src.modules.knowledge.application.interfaces.document_storage import (
    IDocumentStorage,
)


class S3DocumentStorage(IDocumentStorage):
    """S3 文档存储适配器。SDK-First, < 100 行。"""

    def __init__(self, s3_client: Any, *, bucket: str) -> None:
        self._client = s3_client  # boto3.client("s3")
        self._bucket = bucket

    async def upload(self, s3_key: str, content: bytes, *, content_type: str = "application/octet-stream") -> None:
        """上传文档到 S3。"""
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=s3_key,
            Body=content,
            ContentType=content_type,
        )

    async def delete(self, s3_key: str) -> None:
        """删除 S3 文档。"""
        await asyncio.to_thread(
            self._client.delete_object,
            Bucket=self._bucket,
            Key=s3_key,
        )

    async def get_presigned_url(self, s3_key: str, *, expires_in: int = 3600) -> str:
        """生成预签名下载 URL。"""
        url: str = await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": s3_key},
            ExpiresIn=expires_in,
        )
        return url
