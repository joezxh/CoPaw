# -*- coding: utf-8 -*-
"""
Tests for storage factory methods and global singleton.

Covers T-STORAGE-001.7 (factory switching), T-ARCH-001 (dual-track architecture basics).
"""
import os
from unittest.mock import patch

import pytest

from copaw.storage import (
    create_storage_provider,
    get_storage_provider,
    reset_storage_provider,
    ObjectStorageProvider,
)
from copaw.storage.config import StorageConfig
from copaw.storage.filesystem_adapter import FileSystemStorageAdapter
from copaw.storage.base import StorageError, StorageNotFoundError


class TestCreateStorageProvider:
    """T-STORAGE-001.7: Factory method creates the correct adapter."""

    def test_filesystem_backend(self):
        cfg = StorageConfig(backend="filesystem")
        provider = create_storage_provider(cfg)
        assert isinstance(provider, FileSystemStorageAdapter)

    def test_s3_backend(self):
        cfg = StorageConfig(backend="s3")
        provider = create_storage_provider(cfg)
        from copaw.storage.s3_adapter import S3StorageAdapter
        assert isinstance(provider, S3StorageAdapter)

    def test_minio_backend(self):
        cfg = StorageConfig(backend="minio")
        provider = create_storage_provider(cfg)
        from copaw.storage.minio_adapter import MinIOStorageAdapter
        assert isinstance(provider, MinIOStorageAdapter)

    def test_oss_backend(self):
        cfg = StorageConfig(backend="oss")
        provider = create_storage_provider(cfg)
        from copaw.storage.oss_adapter import OSSStorageAdapter
        assert isinstance(provider, OSSStorageAdapter)

    def test_sftp_backend(self):
        cfg = StorageConfig(backend="sftp")
        provider = create_storage_provider(cfg)
        from copaw.storage.sftp_adapter import SFTPStorageAdapter
        assert isinstance(provider, SFTPStorageAdapter)

    def test_invalid_backend_raises(self):
        cfg = StorageConfig(backend="filesystem")
        cfg.backend = "invalid"  # Bypass pydantic validation
        with pytest.raises(ValueError, match="Unsupported storage backend"):
            create_storage_provider(cfg)

    def test_all_adapters_implement_interface(self):
        """T-STORAGE-001.6: All adapters implement ObjectStorageProvider."""
        for backend in ["filesystem", "s3", "minio", "oss", "sftp"]:
            cfg = StorageConfig(backend=backend)  # type: ignore[arg-type]
            provider = create_storage_provider(cfg)
            assert isinstance(provider, ObjectStorageProvider)


class TestGlobalSingleton:
    """Global singleton management."""

    def setup_method(self):
        reset_storage_provider()

    def teardown_method(self):
        reset_storage_provider()

    @pytest.mark.asyncio
    async def test_get_storage_provider_creates_singleton(self):
        with patch.dict(os.environ, {"COPAW_STORAGE_BACKEND": "filesystem"}):
            provider = await get_storage_provider()
            assert isinstance(provider, FileSystemStorageAdapter)

    @pytest.mark.asyncio
    async def test_get_storage_provider_returns_same_instance(self):
        with patch.dict(os.environ, {"COPAW_STORAGE_BACKEND": "filesystem"}):
            p1 = await get_storage_provider()
            p2 = await get_storage_provider()
            assert p1 is p2

    @pytest.mark.asyncio
    async def test_reset_storage_provider(self):
        with patch.dict(os.environ, {"COPAW_STORAGE_BACKEND": "filesystem"}):
            p1 = await get_storage_provider()
            reset_storage_provider()
            p2 = await get_storage_provider()
            assert p1 is not p2


class TestARCH001DualTrackBasics:
    """T-ARCH-001: Dual-track storage architecture basic validation.

    Full integration tests require a running PostgreSQL + object storage.
    Here we verify the structural foundations.
    """

    def test_storage_config_in_enterprise_config(self):
        """EnterpriseConfig should contain a StorageConfig field."""
        from copaw.config.config import EnterpriseConfig
        ent = EnterpriseConfig()
        assert ent.storage is not None
        assert isinstance(ent.storage, StorageConfig)
        assert ent.storage.backend == "filesystem"

    def test_storage_config_custom_values(self):
        """EnterpriseConfig can receive custom storage config."""
        from copaw.config.config import EnterpriseConfig
        ent = EnterpriseConfig(
            storage=StorageConfig(backend="minio", minio_endpoint="minio.corp:9000")
        )
        assert ent.storage.backend == "minio"
        assert ent.storage.minio_endpoint == "minio.corp:9000"

    def test_storage_exception_hierarchy(self):
        """All storage exceptions inherit from a common base for unified handling."""
        from copaw.storage.base import (
            StorageError,
            StorageNotFoundError,
            StoragePermissionError,
            StorageTimeoutError,
        )
        assert issubclass(StorageNotFoundError, StorageError)
        assert issubclass(StoragePermissionError, StorageError)
        assert issubclass(StorageTimeoutError, StorageError)

    def test_metadata_has_tenant_fields(self):
        """ObjectMetadata includes tenant_id and owner_id for dual-track."""
        from copaw.storage.base import ObjectMetadata
        meta = ObjectMetadata(key="test", tenant_id="t1", owner_id="u1")
        assert meta.tenant_id == "t1"
        assert meta.owner_id == "u1"
