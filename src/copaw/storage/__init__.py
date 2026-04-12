# -*- coding: utf-8 -*-
"""CoPaw unified object storage package.

Usage::

    from copaw.storage import get_storage_provider, StorageConfig

    provider = await get_storage_provider()
    meta = await provider.put("key", b"data")
    data = await provider.get("key")
"""

from .base import (
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
from .config import StorageConfig
from .filesystem_adapter import FileSystemStorageAdapter

# Phase 2: Multi-tenant
from .key_builder import StorageKeyBuilder
from .access_control import StorageAccessLevel, StorageACLEntry

# Phase 3: Metadata extraction and search
from .metadata_extractor import MetadataExtractor
from .search_service import StorageSearchService, StorageSearchRequest, StorageSearchResult

__all__ = [
    "ObjectStorageProvider",
    "ObjectMetadata",
    "ListResult",
    "StorageClass",
    "StorageConfig",
    "StorageError",
    "StorageNotFoundError",
    "StoragePermissionError",
    "StorageTimeoutError",
    "StorageConflictError",
    "FileSystemStorageAdapter",
    "create_storage_provider",
    "get_storage_provider",
    "reset_storage_provider",
    # Phase 2: Multi-tenant
    "StorageKeyBuilder",
    "StorageAccessLevel",
    "StorageACLEntry",
    # Phase 3: Metadata
    "MetadataExtractor",
    "StorageSearchService",
    "StorageSearchRequest",
    "StorageSearchResult",
]

# -- Lazy imports for optional backends ----------------------------------- #

_ADAPTER_MAP: dict[str, str] = {
    "filesystem": "copaw.storage.filesystem_adapter:FileSystemStorageAdapter",
    "s3": "copaw.storage.s3_adapter:S3StorageAdapter",
    "minio": "copaw.storage.minio_adapter:MinIOStorageAdapter",
    "oss": "copaw.storage.oss_adapter:OSSStorageAdapter",
    "sftp": "copaw.storage.sftp_adapter:SFTPStorageAdapter",
}

_storage_provider: ObjectStorageProvider | None = None


def _resolve_adapter_cls(backend: str) -> type[ObjectStorageProvider]:
    """Import and return the adapter class for the given backend."""
    spec = _ADAPTER_MAP.get(backend)
    if spec is None:
        raise ValueError(
            f"Unsupported storage backend: {backend!r}. "
            f"Available: {', '.join(_ADAPTER_MAP)}"
        )
    module_path, cls_name = spec.rsplit(":", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, cls_name)


def create_storage_provider(config: StorageConfig) -> ObjectStorageProvider:
    """Factory method — create a storage adapter from the given config.

    Uses lazy imports so that optional SDK dependencies (aioboto3,
    miniopy-async, oss2, asyncssh) are only required when the
    corresponding backend is selected.
    """
    adapter_cls = _resolve_adapter_cls(config.backend)
    return adapter_cls(config)


async def get_storage_provider() -> ObjectStorageProvider:
    """Get or create the global storage provider singleton.

    On first call the provider is created from the current config
    and ``initialize()`` is called.  Subsequent calls return the
    cached instance.
    """
    global _storage_provider
    if _storage_provider is None:
        cfg = StorageConfig.from_env()
        _storage_provider = create_storage_provider(cfg)
        await _storage_provider.initialize()
    return _storage_provider


def reset_storage_provider() -> None:
    """Reset the global singleton — mainly useful for testing."""
    global _storage_provider
    _storage_provider = None
