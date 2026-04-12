# -*- coding: utf-8 -*-
"""
Tests for SFTPStorageAdapter using mocked asyncssh.

Covers T-STORAGE-001.5 (SFTP adapter).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from copaw.storage.base import StorageNotFoundError, StoragePermissionError
from copaw.storage.config import StorageConfig
from copaw.storage.sftp_adapter import SFTPStorageAdapter


@pytest.fixture
def sftp_config():
    return StorageConfig(
        backend="sftp",
        sftp_host="sftp.example.com",
        sftp_port=22,
        sftp_username="testuser",
        sftp_password="testpass",
        sftp_base_dir="/data/copaw",
    )


class TestSFTPAdapterInit:
    """T-STORAGE-001.5: SFTP adapter creation."""

    def test_adapter_creation(self, sftp_config):
        adapter = SFTPStorageAdapter(sftp_config)
        assert adapter._base_dir == "/data/copaw"

    @pytest.mark.asyncio
    async def test_initialize_creates_client(self, sftp_config):
        import sys
        import types
        if "asyncssh" not in sys.modules:
            mock_ssh = types.ModuleType("asyncssh")
            mock_conn = AsyncMock()
            mock_sftp = AsyncMock()
            mock_sftp.mkdir = AsyncMock(return_value=None)
            mock_conn.start_sftp_client = AsyncMock(return_value=mock_sftp)
            mock_ssh.connect = AsyncMock(return_value=mock_conn)
            sys.modules["asyncssh"] = mock_ssh

        adapter = SFTPStorageAdapter(sftp_config)
        await adapter.initialize()
        assert adapter._sftp is not None

    @pytest.mark.asyncio
    async def test_close(self, sftp_config):
        adapter = SFTPStorageAdapter(sftp_config)
        mock_conn = AsyncMock()
        mock_conn.close = MagicMock()
        mock_conn.wait_closed = AsyncMock(return_value=None)
        mock_sftp = AsyncMock()
        mock_sftp.exit = MagicMock()

        adapter._conn = mock_conn
        adapter._sftp = mock_sftp
        await adapter.close()
        assert adapter._sftp is None
        assert adapter._conn is None


class TestSFTPAdapterOperations:
    """T-STORAGE-002: SFTP interface methods with mocked client."""

    @pytest.mark.asyncio
    async def test_put(self, sftp_config):
        adapter = SFTPStorageAdapter(sftp_config)
        mock_sftp = AsyncMock()
        mock_sftp.mkdir = AsyncMock(return_value=None)
        mock_sftp.putfo = AsyncMock(return_value=None)

        # Mock stat for get_metadata
        mock_stat = MagicMock()
        mock_stat.size = 5
        mock_stat.mtime = 1700000000.0
        mock_sftp.stat = AsyncMock(return_value=mock_stat)

        adapter._sftp = mock_sftp
        meta = await adapter.put("test/key.txt", b"hello")
        assert meta.key == "test/key.txt"

    @pytest.mark.asyncio
    async def test_get(self, sftp_config):
        adapter = SFTPStorageAdapter(sftp_config)
        mock_sftp = AsyncMock()
        mock_sftp.getfo = AsyncMock(return_value=None)
        adapter._sftp = mock_sftp

        # Mock the getfo to write to buffer
        from io import BytesIO
        async def fake_getfo(remote, buf):
            buf.write(b"hello")

        mock_sftp.getfo = fake_getfo
        data = await adapter.get("test/key.txt")
        assert data == b"hello"

    @pytest.mark.asyncio
    async def test_get_not_found(self, sftp_config):
        adapter = SFTPStorageAdapter(sftp_config)
        mock_sftp = AsyncMock()

        async def fake_getfo_fail(remote, buf):
            raise Exception("No such file")

        mock_sftp.getfo = fake_getfo_fail
        adapter._sftp = mock_sftp
        with pytest.raises(StorageNotFoundError):
            await adapter.get("missing.txt")

    @pytest.mark.asyncio
    async def test_delete(self, sftp_config):
        adapter = SFTPStorageAdapter(sftp_config)
        mock_sftp = AsyncMock()
        mock_sftp.remove = AsyncMock(return_value=None)
        adapter._sftp = mock_sftp
        result = await adapter.delete("test/key.txt")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists(self, sftp_config):
        adapter = SFTPStorageAdapter(sftp_config)
        mock_sftp = AsyncMock()
        mock_sftp.stat = AsyncMock(return_value=MagicMock())
        adapter._sftp = mock_sftp
        assert await adapter.exists("test/key.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, sftp_config):
        adapter = SFTPStorageAdapter(sftp_config)
        mock_sftp = AsyncMock()
        mock_sftp.stat = AsyncMock(side_effect=Exception("not found"))
        adapter._sftp = mock_sftp
        assert await adapter.exists("missing.txt") is False

    @pytest.mark.asyncio
    async def test_presign_url_not_supported(self, sftp_config):
        """T-STORAGE-004: SFTP does not support pre-signed URLs."""
        adapter = SFTPStorageAdapter(sftp_config)
        with pytest.raises(StoragePermissionError):
            await adapter.presign_url("test/key.txt")

    @pytest.mark.asyncio
    async def test_copy_via_download_upload(self, sftp_config):
        """SFTP copy is implemented as download + upload."""
        adapter = SFTPStorageAdapter(sftp_config)
        mock_sftp = AsyncMock()
        adapter._sftp = mock_sftp

        # Mock get
        from io import BytesIO
        async def fake_getfo(remote, buf):
            buf.write(b"copied content")

        mock_sftp.getfo = fake_getfo
        mock_sftp.mkdir = AsyncMock(return_value=None)
        mock_sftp.putfo = AsyncMock(return_value=None)

        # Mock stat for metadata
        mock_stat = MagicMock()
        mock_stat.size = 14
        mock_stat.mtime = 1700000000.0
        mock_sftp.stat = AsyncMock(return_value=mock_stat)

        meta = await adapter.copy("src.txt", "dst.txt")
        assert meta.key == "dst.txt"
