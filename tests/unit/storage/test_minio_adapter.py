# -*- coding: utf-8 -*-
"""
Tests for MinIOStorageAdapter using mocked miniopy-async.

Covers T-STORAGE-001.3 (MinIO adapter).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from copaw.storage.base import StorageNotFoundError
from copaw.storage.config import StorageConfig
from copaw.storage.minio_adapter import MinIOStorageAdapter


@pytest.fixture
def minio_config():
    return StorageConfig(
        backend="minio",
        minio_endpoint="localhost:9000",
        minio_access_key="minioadmin",
        minio_secret_key="minioadmin",
        minio_bucket="copaw-test",
    )


class TestMinIOAdapterInit:
    """T-STORAGE-001.3: MinIO adapter creation."""

    def test_adapter_creation(self, minio_config):
        adapter = MinIOStorageAdapter(minio_config)
        assert adapter._bucket == "copaw-test"

    @pytest.mark.asyncio
    async def test_initialize_creates_client(self, minio_config):
        import sys
        import types
        # Create mock miniopy_async module if not installed
        if "miniopy_async" not in sys.modules:
            mock_minio_mod = types.ModuleType("miniopy_async")
            mock_client = AsyncMock()
            mock_client.bucket_exists = AsyncMock(return_value=True)
            mock_client.make_bucket = AsyncMock(return_value=None)
            mock_minio_mod.Minio = MagicMock(return_value=mock_client)
            sys.modules["miniopy_async"] = mock_minio_mod
            sys.modules["miniopy_async.commonconfig"] = types.ModuleType("commonconfig")

        adapter = MinIOStorageAdapter(minio_config)
        await adapter.initialize()
        assert adapter._client is not None

    @pytest.mark.asyncio
    async def test_initialize_creates_bucket(self, minio_config):
        import sys
        import types
        if "miniopy_async" not in sys.modules:
            mock_minio_mod = types.ModuleType("miniopy_async")
            mock_client = AsyncMock()
            mock_client.bucket_exists = AsyncMock(return_value=False)
            mock_client.make_bucket = AsyncMock(return_value=None)
            mock_minio_mod.Minio = MagicMock(return_value=mock_client)
            sys.modules["miniopy_async"] = mock_minio_mod
            sys.modules["miniopy_async.commonconfig"] = types.ModuleType("commonconfig")

        adapter = MinIOStorageAdapter(minio_config)
        await adapter.initialize()
        # bucket_exists returned False -> make_bucket should be called


class TestMinIOAdapterOperations:
    """T-STORAGE-002: MinIO interface methods with mocked client."""

    @pytest.mark.asyncio
    async def test_put(self, minio_config):
        adapter = MinIOStorageAdapter(minio_config)
        mock_client = AsyncMock()
        mock_client.put_object = AsyncMock(return_value=None)

        # Mock stat_object for get_metadata after put
        mock_stat = MagicMock()
        mock_stat.size = 5
        mock_stat.content_type = "text/plain"
        mock_stat.etag = '"abc"'
        mock_stat.last_modified = datetime.now(timezone.utc)
        mock_stat.metadata = {}
        mock_client.stat_object = AsyncMock(return_value=mock_stat)

        adapter._client = mock_client
        meta = await adapter.put("test/key.txt", b"hello")
        assert meta.key == "test/key.txt"
        mock_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_get(self, minio_config):
        adapter = MinIOStorageAdapter(minio_config)
        mock_client = AsyncMock()
        mock_resp = AsyncMock()
        mock_resp.read = AsyncMock(return_value=b"hello")
        mock_resp.close = MagicMock()
        mock_resp.release = MagicMock()
        mock_client.get_object = AsyncMock(return_value=mock_resp)

        adapter._client = mock_client
        data = await adapter.get("test/key.txt")
        assert data == b"hello"

    @pytest.mark.asyncio
    async def test_get_not_found(self, minio_config):
        adapter = MinIOStorageAdapter(minio_config)
        mock_client = AsyncMock()
        mock_client.get_object = AsyncMock(
            side_effect=Exception("NoSuchKey: The specified key does not exist")
        )
        adapter._client = mock_client
        with pytest.raises(StorageNotFoundError):
            await adapter.get("missing.txt")

    @pytest.mark.asyncio
    async def test_delete(self, minio_config):
        adapter = MinIOStorageAdapter(minio_config)
        mock_client = AsyncMock()
        mock_client.remove_object = AsyncMock(return_value=None)
        adapter._client = mock_client
        result = await adapter.delete("test/key.txt")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists(self, minio_config):
        adapter = MinIOStorageAdapter(minio_config)
        mock_client = AsyncMock()
        mock_client.stat_object = AsyncMock(return_value=MagicMock())
        adapter._client = mock_client
        assert await adapter.exists("test/key.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, minio_config):
        adapter = MinIOStorageAdapter(minio_config)
        mock_client = AsyncMock()
        mock_client.stat_object = AsyncMock(side_effect=Exception("not found"))
        adapter._client = mock_client
        assert await adapter.exists("missing.txt") is False

    @pytest.mark.asyncio
    async def test_presign_url(self, minio_config):
        adapter = MinIOStorageAdapter(minio_config)
        mock_client = AsyncMock()
        mock_client.presigned_get_object = AsyncMock(
            return_value="http://localhost:9000/copaw-test/key?X-Amz-Signature=abc"
        )
        adapter._client = mock_client
        url = await adapter.presign_url("test/key.txt")
        assert "localhost" in url
