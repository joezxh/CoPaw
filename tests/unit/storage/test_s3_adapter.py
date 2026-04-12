# -*- coding: utf-8 -*-
"""
Tests for S3StorageAdapter using mocked aioboto3.

Covers T-STORAGE-001.2 (S3 adapter), T-STORAGE-002 (interface methods).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from copaw.storage.base import StorageNotFoundError, StorageClass
from copaw.storage.config import StorageConfig
from copaw.storage.s3_adapter import S3StorageAdapter


@pytest.fixture
def s3_config():
    return StorageConfig(
        backend="s3",
        s3_access_key="test-key",
        s3_secret_key="test-secret",
        s3_region="us-east-1",
        s3_bucket="test-bucket",
    )


@pytest.fixture
def mock_s3_client():
    """Mock the aioboto3 S3 client."""
    client = AsyncMock()
    client.exceptions = MagicMock()
    client.exceptions.NoSuchKey = type("NoSuchKey", (Exception,), {})
    return client


class TestS3AdapterInit:
    """T-STORAGE-001.2: S3 adapter creation."""

    def test_adapter_creation(self, s3_config):
        adapter = S3StorageAdapter(s3_config)
        assert adapter._bucket == "test-bucket"

    @pytest.mark.asyncio
    async def test_initialize_creates_client(self, s3_config, mock_s3_client):
        import sys
        import types
        # Create mock aioboto3 module if not installed
        if "aioboto3" not in sys.modules:
            mock_aioboto3 = types.ModuleType("aioboto3")
            mock_session = MagicMock()
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3_client)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_session.client.return_value = mock_ctx
            mock_aioboto3.Session = MagicMock(return_value=mock_session)
            sys.modules["aioboto3"] = mock_aioboto3

        mock_s3_client.head_bucket = AsyncMock(return_value={})

        adapter = S3StorageAdapter(s3_config)
        await adapter.initialize()
        assert adapter._client is not None

    @pytest.mark.asyncio
    async def test_close(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.__aexit__ = AsyncMock(return_value=False)
        await adapter.close()
        assert adapter._client is None


class TestS3AdapterOperations:
    """T-STORAGE-002: S3 interface methods with mocked client."""

    @pytest.mark.asyncio
    async def test_put(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.put_object = AsyncMock(return_value={})
        mock_s3_client.head_object = AsyncMock(return_value={
            "ContentLength": 5,
            "ContentType": "application/octet-stream",
            "ETag": '"abc123"',
            "StorageClass": "STANDARD",
        })
        meta = await adapter.put("test/key.txt", b"hello")
        assert meta.key == "test/key.txt"
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_get(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_body = AsyncMock()
        mock_body.read = AsyncMock(return_value=b"hello")
        mock_s3_client.get_object = AsyncMock(return_value={"Body": mock_body})
        data = await adapter.get("test/key.txt")
        assert data == b"hello"

    @pytest.mark.asyncio
    async def test_get_not_found(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.get_object = AsyncMock(side_effect=Exception("NoSuchKey"))
        with pytest.raises(StorageNotFoundError):
            await adapter.get("missing/key.txt")

    @pytest.mark.asyncio
    async def test_delete(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.delete_object = AsyncMock(return_value={})
        result = await adapter.delete("test/key.txt")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.head_object = AsyncMock(return_value={})
        assert await adapter.exists("test/key.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.head_object = AsyncMock(side_effect=Exception("404"))
        assert await adapter.exists("missing.txt") is False

    @pytest.mark.asyncio
    async def test_copy(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.copy_object = AsyncMock(return_value={})
        mock_s3_client.head_object = AsyncMock(return_value={
            "ContentLength": 5,
            "ContentType": "text/plain",
            "ETag": '"xyz"',
            "StorageClass": "STANDARD",
        })
        meta = await adapter.copy("src.txt", "dst.txt")
        assert meta.key == "dst.txt"

    @pytest.mark.asyncio
    async def test_list_objects(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.list_objects_v2 = AsyncMock(return_value={
            "Contents": [
                {"Key": "test/a.txt", "Size": 10, "ETag": '"a"', "StorageClass": "STANDARD"},
                {"Key": "test/b.txt", "Size": 20, "ETag": '"b"', "StorageClass": "STANDARD"},
            ],
            "IsTruncated": False,
        })
        result = await adapter.list_objects("test/")
        assert len(result.objects) == 2
        assert result.is_truncated is False

    @pytest.mark.asyncio
    async def test_presign_url(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.generate_presigned_url = AsyncMock(
            return_value="https://s3.amazonaws.com/test-bucket/key?signature=abc"
        )
        url = await adapter.presign_url("test/key.txt")
        assert url.startswith("https://")

    @pytest.mark.asyncio
    async def test_put_metadata(self, s3_config, mock_s3_client):
        adapter = S3StorageAdapter(s3_config)
        adapter._client = mock_s3_client
        mock_s3_client.head_object = AsyncMock(return_value={
            "ContentLength": 5,
            "ContentType": "text/plain",
            "ETag": '"abc"',
            "StorageClass": "STANDARD",
            "Metadata": {"existing": "value"},
        })
        mock_s3_client.copy_object = AsyncMock(return_value={})
        meta = await adapter.put_metadata("test/key.txt", {"new_key": "new_val"})
        assert meta.key == "test/key.txt"
