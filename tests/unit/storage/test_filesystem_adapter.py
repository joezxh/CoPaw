# -*- coding: utf-8 -*-
"""
Tests for FileSystemStorageAdapter.

Covers T-STORAGE-001.1 (FileSystem adapter), T-STORAGE-002 (interface methods),
T-STORAGE-003 (performance metrics), T-STORAGE-004 (error handling).
"""
import asyncio
import hashlib
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from copaw.storage.base import (
    ObjectMetadata,
    StorageClass,
    StorageNotFoundError,
    StoragePermissionError,
)
from copaw.storage.config import StorageConfig
from copaw.storage.filesystem_adapter import FileSystemStorageAdapter


@pytest.fixture
def tmp_storage_dir():
    """Create a temporary directory for storage tests."""
    d = tempfile.mkdtemp(prefix="copaw_test_storage_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def storage(tmp_storage_dir):
    """Create a FileSystemStorageAdapter with a temp directory."""
    cfg = StorageConfig(filesystem_base_dir=tmp_storage_dir)
    adapter = FileSystemStorageAdapter(cfg)
    return adapter


# ==================== T-STORAGE-001.1: FileSystem Adapter ====================


class TestFileSystemPut:
    """T-STORAGE-001.1 + T-STORAGE-002: put operation."""

    @pytest.mark.asyncio
    async def test_put_bytes(self, storage):
        meta = await storage.put("test/file.txt", b"hello world")
        assert isinstance(meta, ObjectMetadata)
        assert meta.key == "test/file.txt"
        assert meta.size == 11
        assert meta.content_type == "application/octet-stream"

    @pytest.mark.asyncio
    async def test_put_with_content_type(self, storage):
        meta = await storage.put(
            "data.json",
            b'{"key": "val"}',
            content_type="application/json",
        )
        assert meta.content_type == "application/json"

    @pytest.mark.asyncio
    async def test_put_with_metadata(self, storage):
        meta = await storage.put(
            "doc.md",
            b"# Title",
            metadata={"author": "test", "version": "1.0"},
        )
        assert meta.custom_metadata.get("author") == "test"

    @pytest.mark.asyncio
    async def test_put_creates_directories(self, storage):
        meta = await storage.put(
            "deep/nested/path/file.txt",
            b"deep content",
        )
        assert meta.key == "deep/nested/path/file.txt"

    @pytest.mark.asyncio
    async def test_put_stream(self, storage):
        """Upload via async iterator."""

        async def data_stream():
            yield b"chunk1"
            yield b"chunk2"

        meta = await storage.put("streamed.bin", data_stream())
        assert meta.size == len(b"chunk1chunk2")

    @pytest.mark.asyncio
    async def test_put_overwrite(self, storage):
        await storage.put("overwrite.txt", b"original")
        await storage.put("overwrite.txt", b"updated")
        data = await storage.get("overwrite.txt")
        assert data == b"updated"

    @pytest.mark.asyncio
    async def test_put_etag(self, storage):
        """ETag should be MD5 of content."""
        content = b"test etag content"
        meta = await storage.put("etag_test.txt", content)
        expected_etag = hashlib.md5(content).hexdigest()
        assert meta.etag == expected_etag


class TestFileSystemGet:
    """T-STORAGE-002: get operation."""

    @pytest.mark.asyncio
    async def test_get_existing(self, storage):
        await storage.put("read.txt", b"read me")
        data = await storage.get("read.txt")
        assert data == b"read me"

    @pytest.mark.asyncio
    async def test_get_not_found(self, storage):
        with pytest.raises(StorageNotFoundError):
            await storage.get("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_get_binary_content(self, storage):
        binary_data = bytes(range(256))
        await storage.put("binary.bin", binary_data)
        data = await storage.get("binary.bin")
        assert data == binary_data

    @pytest.mark.asyncio
    async def test_get_large_content(self, storage):
        """T-STORAGE-003: Large file read."""
        large_data = b"x" * (5 * 1024 * 1024)  # 5 MB
        await storage.put("large.bin", large_data)
        data = await storage.get("large.bin")
        assert len(data) == 5 * 1024 * 1024


class TestFileSystemGetStream:
    """T-STORAGE-002: get_stream operation."""

    @pytest.mark.asyncio
    async def test_get_stream(self, storage):
        content = b"streaming content test"
        await storage.put("stream.txt", content)
        chunks = []
        async for chunk in storage.get_stream("stream.txt"):
            chunks.append(chunk)
        assert b"".join(chunks) == content

    @pytest.mark.asyncio
    async def test_get_stream_not_found(self, storage):
        with pytest.raises(StorageNotFoundError):
            async for _ in storage.get_stream("nope.txt"):
                pass


class TestFileSystemDelete:
    """T-STORAGE-002: delete operation."""

    @pytest.mark.asyncio
    async def test_delete_existing(self, storage):
        await storage.put("del.txt", b"delete me")
        result = await storage.delete("del.txt")
        assert result is True
        assert not await storage.exists("del.txt")

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, storage):
        result = await storage.delete("nonexistent.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_removes_metadata(self, storage, tmp_storage_dir):
        await storage.put("meta_del.txt", b"data", metadata={"keep": "yes"})
        await storage.delete("meta_del.txt")
        # Sidecar .meta.json should also be removed
        base = Path(tmp_storage_dir)
        meta_file = base / "meta_del.txt.meta.json"
        assert not meta_file.exists()


class TestFileSystemExists:
    """T-STORAGE-002: exists operation."""

    @pytest.mark.asyncio
    async def test_exists_true(self, storage):
        await storage.put("exists.txt", b"yes")
        assert await storage.exists("exists.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false(self, storage):
        assert await storage.exists("nope.txt") is False


class TestFileSystemCopy:
    """T-STORAGE-002: copy operation."""

    @pytest.mark.asyncio
    async def test_copy(self, storage):
        await storage.put("src.txt", b"copy source")
        meta = await storage.copy("src.txt", "dst.txt")
        assert meta.key == "dst.txt"
        data = await storage.get("dst.txt")
        assert data == b"copy source"

    @pytest.mark.asyncio
    async def test_copy_not_found(self, storage):
        with pytest.raises(StorageNotFoundError):
            await storage.copy("missing.txt", "dst.txt")

    @pytest.mark.asyncio
    async def test_copy_preserves_metadata(self, storage):
        await storage.put("src.json", b"{}", metadata={"type": "config"})
        await storage.copy("src.json", "dst.json")
        meta = await storage.get_metadata("dst.json")
        assert meta.custom_metadata.get("type") == "config"


class TestFileSystemListObjects:
    """T-STORAGE-002: list_objects operation."""

    @pytest.mark.asyncio
    async def test_list_empty(self, storage):
        result = await storage.list_objects("nonexistent/")
        assert len(result.objects) == 0

    @pytest.mark.asyncio
    async def test_list_with_objects(self, storage):
        await storage.put("list/a.txt", b"a")
        await storage.put("list/b.txt", b"b")
        await storage.put("list/c.txt", b"c")
        result = await storage.list_objects("list/")
        assert len(result.objects) == 3

    @pytest.mark.asyncio
    async def test_list_prefix_filter(self, storage):
        await storage.put("docs/readme.md", b"readme")
        await storage.put("code/main.py", b"main")
        result = await storage.list_objects("docs/")
        assert len(result.objects) == 1
        assert result.objects[0].key.startswith("docs/")

    @pytest.mark.asyncio
    async def test_list_pagination(self, storage):
        for i in range(5):
            await storage.put(f"page/{i}.txt", f"item{i}".encode())
        result = await storage.list_objects("page/", max_keys=3)
        assert len(result.objects) <= 3
        if result.is_truncated:
            assert result.continuation_token


class TestFileSystemMetadata:
    """T-STORAGE-002: get_metadata / put_metadata."""

    @pytest.mark.asyncio
    async def test_get_metadata(self, storage):
        await storage.put("meta.txt", b"test", content_type="text/plain")
        meta = await storage.get_metadata("meta.txt")
        assert meta.key == "meta.txt"
        assert meta.size == 4
        assert meta.content_type == "text/plain"

    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self, storage):
        with pytest.raises(StorageNotFoundError):
            await storage.get_metadata("missing.txt")

    @pytest.mark.asyncio
    async def test_put_metadata(self, storage):
        await storage.put("upd.txt", b"data")
        meta = await storage.put_metadata("upd.txt", {"new_key": "new_val"})
        assert meta.custom_metadata.get("new_key") == "new_val"

    @pytest.mark.asyncio
    async def test_put_metadata_merges(self, storage):
        await storage.put("merge.txt", b"data", metadata={"k1": "v1"})
        meta = await storage.put_metadata("merge.txt", {"k2": "v2"})
        assert meta.custom_metadata.get("k1") == "v1"
        assert meta.custom_metadata.get("k2") == "v2"


class TestFileSystemPresignUrl:
    """T-STORAGE-002: presign_url for FileSystem adapter."""

    @pytest.mark.asyncio
    async def test_presign_url_returns_file_uri(self, storage):
        await storage.put("presign.txt", b"data")
        url = await storage.presign_url("presign.txt")
        assert url.startswith("file:///")

    @pytest.mark.asyncio
    async def test_presign_url_not_found(self, storage):
        with pytest.raises(StorageNotFoundError):
            await storage.presign_url("missing.txt")


class TestFileSystemSecurity:
    """T-STORAGE-004: Path traversal prevention."""

    @pytest.mark.asyncio
    async def test_path_traversal_prevented(self, storage):
        with pytest.raises(StoragePermissionError):
            await storage.put("../../etc/passwd", b"hack")

    @pytest.mark.asyncio
    async def test_absolute_path_prevented(self, storage):
        with pytest.raises(StoragePermissionError):
            await storage.get("/etc/passwd")


class TestFileSystemCompatibility:
    """T-ARCH-001: FileSystem adapter 100% compatible with ~/.copaw/."""

    @pytest.mark.asyncio
    async def test_copaw_working_dir_layout(self, tmp_storage_dir):
        """Verify the adapter works with typical ~/.copaw/ file layout."""
        cfg = StorageConfig(filesystem_base_dir=tmp_storage_dir)
        adapter = FileSystemStorageAdapter(cfg)

        # Simulate typical CoPaw files
        await adapter.put("agents/default/agent.json", b'{"name": "test"}')
        await adapter.put("skill_pool/weather/skill.json", b'{"skill": "weather"}')
        await adapter.put("memory/default/chat.md", b"# Chat Memory")

        # Verify they're on the filesystem
        base = Path(tmp_storage_dir)
        assert (base / "agents/default/agent.json").exists()
        assert (base / "skill_pool/weather/skill.json").exists()
        assert (base / "memory/default/chat.md").exists()

        # Read back through adapter
        data = await adapter.get("agents/default/agent.json")
        assert b'"name": "test"' in data
