# -*- coding: utf-8 -*-
"""
Tests for storage REST API endpoints.

Covers T-STORAGE-002 (API interface verification).
"""
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from copaw.storage.config import StorageConfig
from copaw.storage.filesystem_adapter import FileSystemStorageAdapter
from copaw.app.routers.storage import router


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp(prefix="copaw_test_api_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def app_with_storage(tmp_dir):
    """Create a FastAPI app with the storage router and a real FileSystem adapter."""
    application = FastAPI()
    application.include_router(router)

    cfg = StorageConfig(filesystem_base_dir=tmp_dir)
    adapter = FileSystemStorageAdapter(cfg)
    application.state.storage = adapter

    return application


@pytest.fixture
async def client(app_with_storage):
    transport = ASGITransport(app=app_with_storage)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestStorageAPIUpload:
    """PUT /enterprise/storage/{key} endpoint."""

    @pytest.mark.asyncio
    async def test_upload_file(self, client):
        response = await client.put(
            "/enterprise/storage/test/upload.txt",
            files={"file": ("upload.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "test/upload.txt"
        assert data["size"] == 11

    @pytest.mark.asyncio
    async def test_upload_nested_path(self, client):
        response = await client.put(
            "/enterprise/storage/agents/default/agent.json",
            files={"file": ("agent.json", b'{"name": "test"}', "application/json")},
        )
        assert response.status_code == 200


class TestStorageAPIDownload:
    """GET /enterprise/storage/{key} endpoint."""

    @pytest.mark.asyncio
    async def test_download_file(self, client):
        # Upload first
        await client.put(
            "/enterprise/storage/test/download.txt",
            files={"file": ("download.txt", b"download me", "text/plain")},
        )
        # Then download
        response = await client.get("/enterprise/storage/test/download.txt")
        assert response.status_code == 200
        assert response.content == b"download me"

    @pytest.mark.asyncio
    async def test_download_not_found(self, client):
        response = await client.get("/enterprise/storage/nonexistent.txt")
        assert response.status_code == 404


class TestStorageAPIDelete:
    """DELETE /enterprise/storage/{key} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_file(self, client):
        # Upload first
        await client.put(
            "/enterprise/storage/test/delete.txt",
            files={"file": ("delete.txt", b"delete me", "text/plain")},
        )
        response = await client.delete("/enterprise/storage/test/delete.txt")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        response = await client.delete("/enterprise/storage/nonexistent.txt")
        assert response.status_code == 404


class TestStorageAPIList:
    """GET /enterprise/storage/list endpoint."""

    @pytest.mark.asyncio
    async def test_list_objects(self, client):
        # Upload some files
        for i in range(3):
            await client.put(
                f"/enterprise/storage/items/{i}.txt",
                files={"file": (f"{i}.txt", f"item{i}".encode(), "text/plain")},
            )
        response = await client.get(
            "/enterprise/storage/list",
            params={"prefix": "items/"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["objects"]) == 3

    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        response = await client.get(
            "/enterprise/storage/list",
            params={"prefix": "nonexistent_dir/"},
        )
        assert response.status_code == 200
        assert len(response.json()["objects"]) == 0


class TestStorageAPIMetadata:
    """GET /enterprise/storage/metadata/{key} endpoint."""

    @pytest.mark.asyncio
    async def test_get_metadata(self, client):
        await client.put(
            "/enterprise/storage/meta/test.txt",
            files={"file": ("test.txt", b"metadata test", "text/plain")},
        )
        response = await client.get("/enterprise/storage/metadata/meta/test.txt")
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "meta/test.txt"
        assert data["size"] == 13

    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self, client):
        response = await client.get("/enterprise/storage/metadata/nonexistent.txt")
        assert response.status_code == 404


class TestStorageAPIPresign:
    """GET /enterprise/storage/presign/{key} endpoint."""

    @pytest.mark.asyncio
    async def test_presign_url(self, client):
        await client.put(
            "/enterprise/storage/presign/test.txt",
            files={"file": ("test.txt", b"presign data", "text/plain")},
        )
        response = await client.get("/enterprise/storage/presign/presign/test.txt")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["expires_in"] == 3600


class TestStorageAPIStats:
    """GET /enterprise/storage/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats(self, client):
        response = await client.get("/enterprise/storage/stats")
        assert response.status_code == 200
        data = response.json()
        assert "backend" in data
        assert "bucket" in data
        assert "presign_enabled" in data


class TestStorageAPINoStorage:
    """Test API when storage is not configured."""

    @pytest.mark.asyncio
    async def test_returns_503_when_no_storage(self):
        application = FastAPI()
        application.include_router(router)
        application.state.storage = None

        transport = ASGITransport(app=application)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            # Upload requires storage -> should return 503
            response = await c.put(
                "/enterprise/storage/test.txt",
                files={"file": ("test.txt", b"data", "text/plain")},
            )
            assert response.status_code == 503
