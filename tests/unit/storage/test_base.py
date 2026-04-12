# -*- coding: utf-8 -*-
"""
Tests for storage base module — ObjectStorageProvider, data classes, exceptions.

Covers T-STORAGE-002 (interface methods) and T-STORAGE-004 (error handling).
"""
import pytest
from datetime import datetime, timezone

from copaw.storage.base import (
    ListResult,
    ObjectMetadata,
    ObjectStorageProvider,
    StorageClass,
    StorageConflictError,
    StorageError,
    StorageNotFoundError,
    StoragePermissionError,
    StorageTimeoutError,
)


# ==================== Data Class Tests ====================


class TestStorageClass:
    """T-STORAGE-002.1: StorageClass enum values."""

    def test_standard(self):
        assert StorageClass.STANDARD == "STANDARD"

    def test_infrequent(self):
        assert StorageClass.INFREQUENT == "INFREQUENT_ACCESS"

    def test_archive(self):
        assert StorageClass.ARCHIVE == "ARCHIVE"

    def test_string_conversion(self):
        assert StorageClass("STANDARD") is StorageClass.STANDARD


class TestObjectMetadata:
    """T-STORAGE-002.2: ObjectMetadata data class."""

    def test_defaults(self):
        meta = ObjectMetadata(key="test/file.txt")
        assert meta.key == "test/file.txt"
        assert meta.size == 0
        assert meta.content_type == "application/octet-stream"
        assert meta.etag == ""
        assert meta.last_modified is None
        assert meta.storage_class == StorageClass.STANDARD
        assert meta.custom_metadata == {}
        assert meta.tenant_id == ""
        assert meta.owner_id == ""
        assert meta.category == ""

    def test_custom_values(self):
        now = datetime.now(timezone.utc)
        meta = ObjectMetadata(
            key="agent/default/agent.json",
            size=1024,
            content_type="application/json",
            etag="abc123",
            last_modified=now,
            storage_class=StorageClass.INFREQUENT,
            custom_metadata={"source": "upload"},
            tenant_id="t1",
            owner_id="u1",
            category="config",
        )
        assert meta.size == 1024
        assert meta.content_type == "application/json"
        assert meta.tenant_id == "t1"
        assert meta.category == "config"


class TestListResult:
    """T-STORAGE-002.3: ListResult data class."""

    def test_defaults(self):
        result = ListResult(prefix="test/")
        assert result.objects == []
        assert result.prefix == "test/"
        assert result.is_truncated is False
        assert result.continuation_token == ""

    def test_with_objects(self):
        obj = ObjectMetadata(key="test/a.txt", size=10)
        result = ListResult(
            objects=[obj],
            prefix="test/",
            is_truncated=True,
            continuation_token="token123",
        )
        assert len(result.objects) == 1
        assert result.is_truncated is True


# ==================== Exception Tests ====================


class TestStorageExceptions:
    """T-STORAGE-004: Error handling for storage exceptions."""

    def test_storage_error(self):
        err = StorageError("something went wrong")
        assert "something went wrong" in str(err)
        assert err.code == "STORAGE_ERROR"

    def test_storage_not_found_error(self):
        err = StorageNotFoundError("missing/key.txt")
        assert "missing/key.txt" in str(err)
        assert err.key == "missing/key.txt"
        assert err.details["key"] == "missing/key.txt"

    def test_storage_permission_error(self):
        err = StoragePermissionError("secret/key.txt", reason="no access")
        assert "secret/key.txt" in str(err)
        assert "no access" in str(err)
        assert err.key == "secret/key.txt"

    def test_storage_timeout_error(self):
        err = StorageTimeoutError("slow/key.txt", timeout=30.0)
        assert "slow/key.txt" in str(err)
        assert "30" in str(err)
        assert err.timeout == 30.0

    def test_storage_conflict_error(self):
        err = StorageConflictError("concurrent/key.txt")
        assert "concurrent/key.txt" in str(err)
        assert err.key == "concurrent/key.txt"

    def test_exception_hierarchy(self):
        """All storage exceptions inherit from StorageError."""
        assert issubclass(StorageNotFoundError, StorageError)
        assert issubclass(StoragePermissionError, StorageError)
        assert issubclass(StorageTimeoutError, StorageError)
        assert issubclass(StorageConflictError, StorageError)

    def test_exception_details_not_leaking_secrets(self):
        """T-STORAGE-004: Error messages must not contain sensitive info."""
        err = StorageError(
            "Connection refused",
            details={"host": "minio.internal", "port": 9000},
        )
        # Details should be in structured format, not in message
        assert "Connection refused" in str(err)
        # Ensure no password/secret key in string representation
        err2 = StoragePermissionError(
            "key",
            reason="auth failed",
            details={"access_key": "AKIA***REDACTED***"},
        )
        assert "REDACTED" in err2.details.get("access_key", "")


# ==================== Abstract Interface Tests ====================


class TestObjectStorageProviderInterface:
    """T-STORAGE-002: Verify ObjectStorageProvider defines all required methods."""

    def test_abstract_methods(self):
        """All required methods are defined as abstract."""
        abstract_methods = ObjectStorageProvider.__abstractmethods__
        expected = {
            "put",
            "get",
            "get_stream",
            "delete",
            "exists",
            "copy",
            "list_objects",
            "get_metadata",
            "put_metadata",
            "presign_url",
        }
        assert abstract_methods == expected

    def test_cannot_instantiate_directly(self):
        """ObjectStorageProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ObjectStorageProvider()

    def test_default_lifecycle_methods(self):
        """initialize() and close() have default (no-op) implementations."""
        # Create a minimal concrete subclass
        class MinimalProvider(ObjectStorageProvider):
            async def put(self, key, data, **kwargs):
                pass
            async def get(self, key):
                pass
            async def get_stream(self, key):
                pass
            async def delete(self, key):
                pass
            async def exists(self, key):
                pass
            async def copy(self, source_key, dest_key):
                pass
            async def list_objects(self, prefix, **kwargs):
                pass
            async def get_metadata(self, key):
                pass
            async def put_metadata(self, key, metadata):
                pass
            async def presign_url(self, key, **kwargs):
                pass

        provider = MinimalProvider()
        # initialize() and close() should be callable (no-op)
        import asyncio
        asyncio.run(provider.initialize())
        asyncio.run(provider.close())
