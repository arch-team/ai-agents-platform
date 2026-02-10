"""S3DocumentStorage 单元测试。"""

import pytest
from unittest.mock import MagicMock

from src.modules.knowledge.infrastructure.external.s3_document_storage import S3DocumentStorage


@pytest.mark.unit
class TestS3DocumentStorage:
    @pytest.mark.asyncio
    async def test_upload(self) -> None:
        client = MagicMock()
        storage = S3DocumentStorage(client, bucket="test-bucket")
        await storage.upload("kb/1/test.pdf", b"data", content_type="application/pdf")
        client.put_object.assert_called_once_with(
            Bucket="test-bucket", Key="kb/1/test.pdf", Body=b"data", ContentType="application/pdf",
        )

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        client = MagicMock()
        storage = S3DocumentStorage(client, bucket="test-bucket")
        await storage.delete("kb/1/test.pdf")
        client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="kb/1/test.pdf")

    @pytest.mark.asyncio
    async def test_get_presigned_url(self) -> None:
        client = MagicMock()
        client.generate_presigned_url.return_value = "https://s3.example.com/signed"
        storage = S3DocumentStorage(client, bucket="test-bucket")
        url = await storage.get_presigned_url("kb/1/test.pdf", expires_in=600)
        assert url == "https://s3.example.com/signed"
        client.generate_presigned_url.assert_called_once()
