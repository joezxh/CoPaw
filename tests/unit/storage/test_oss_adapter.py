# -*- coding: utf-8 -*-
"""
Tests for OSSStorageAdapter using mocked oss2.

Covers T-STORAGE-001.4 (OSS adapter).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from copaw.storage.base import StorageNotFoundError
from copaw.storage.config import StorageConfig
from copaw.storage.oss_adapter import OSSStorageAdapter


@pytest.fixture
def oss_config():
    return StorageConfig(
        backend="oss",
        oss_endpoint="https://oss-cn-hangzhou.aliyuncs.com",
        oss_access_key_id="test-ak",
        oss_access_key_secret="test-sk",
        oss_bucket_name="copaw-test",
    )


class TestOSSAdapterInit:
    """T-STORAGE-001.4: OSS adapter creation."""

    def test_adapter_creation(self, oss_config):
        adapter = OSSStorageAdapter(oss_config)
        assert adapter._bucket_name == "copaw-test"

    @pytest.mark.asyncio
    async def test_initialize_creates_client(self, oss_config):
        import sys
        import types
        if "oss2" not in sys.modules:
            mock_oss2 = types.ModuleType("oss2")
            mock_auth = MagicMock()
            mock_oss2.Auth = MagicMock(return_value=mock_auth)
            mock_bucket = MagicMock()
            mock_bucket.exists.return_value = True
            mock_oss2.Bucket = MagicMock(return_value=mock_bucket)
            mock_oss2.exceptions = types.ModuleType("exceptions")
            mock_oss2.exceptions.NoSuchBucket = type("NoSuchBucket", (Exception,), {})
            sys.modules["oss2"] = mock_oss2
            sys.modules["oss2.exceptions"] = mock_oss2.exceptions

        adapter = OSSStorageAdapter(oss_config)
        await adapter.initialize()
        assert adapter._bucket is not None


class TestOSSAdapterOperations:
    """T-STORAGE-002: OSS interface methods with mocked client."""

    @pytest.mark.asyncio
    async def test_put(self, oss_config):
        adapter = OSSStorageAdapter(oss_config)
        mock_bucket = MagicMock()
        mock_bucket.put_object = MagicMock(return_value=MagicMock())

        # Mock head_object for get_metadata
        mock_info = MagicMock()
        mock_info.content_length = 5
        mock_info.content_type = "application/octet-stream"
        mock_info.etag = '"abc"'
        mock_info.headers = {}
        mock_bucket.head_object = MagicMock(return_value=mock_info)

        adapter._bucket = mock_bucket
        meta = await adapter.put("test/key.txt", b"hello")
        assert meta.key == "test/key.txt"

    @pytest.mark.asyncio
    async def test_get(self, oss_config):
        adapter = OSSStorageAdapter(oss_config)
        mock_bucket = MagicMock()
        mock_result = MagicMock()
        mock_result.read.return_value = b"hello"
        mock_bucket.get_object.return_value = mock_result

        adapter._bucket = mock_bucket
        data = await adapter.get("test/key.txt")
        assert data == b"hello"

    @pytest.mark.asyncio
    async def test_get_not_found(self, oss_config):
        adapter = OSSStorageAdapter(oss_config)
        mock_bucket = MagicMock()
        mock_bucket.get_object.side_effect = Exception("NoSuchKey")
        adapter._bucket = mock_bucket
        with pytest.raises(StorageNotFoundError):
            await adapter.get("missing.txt")

    @pytest.mark.asyncio
    async def test_delete(self, oss_config):
        adapter = OSSStorageAdapter(oss_config)
        mock_bucket = MagicMock()
        mock_bucket.delete_object = MagicMock(return_value=None)
        adapter._bucket = mock_bucket
        result = await adapter.delete("test/key.txt")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists(self, oss_config):
        adapter = OSSStorageAdapter(oss_config)
        mock_bucket = MagicMock()
        mock_bucket.object_exists.return_value = True
        adapter._bucket = mock_bucket
        assert await adapter.exists("test/key.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, oss_config):
        adapter = OSSStorageAdapter(oss_config)
        mock_bucket = MagicMock()
        mock_bucket.object_exists.return_value = False
        adapter._bucket = mock_bucket
        assert await adapter.exists("missing.txt") is False

    @pytest.mark.asyncio
    async def test_presign_url(self, oss_config):
        adapter = OSSStorageAdapter(oss_config)
        mock_bucket = MagicMock()
        mock_bucket.sign_url.return_value = "https://oss.example.com/signed?url=abc"
        adapter._bucket = mock_bucket
        url = await adapter.presign_url("test/key.txt")
        assert "oss.example.com" in url
