# -*- coding: utf-8 -*-
"""
Unified object storage interface and data classes.

All storage backends must implement the ObjectStorageProvider abstract class.
This module also defines shared data classes, enums, and storage-specific exceptions.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import AsyncIterator, Optional

from agentscope_runtime.engine.schemas.exception import (
    AgentRuntimeErrorException,
)


# ==================== Enums ====================


class StorageClass(str, Enum):
    """Object storage class – maps to S3/MinIO storage classes."""

    STANDARD = "STANDARD"
    INFREQUENT = "INFREQUENT_ACCESS"
    ARCHIVE = "ARCHIVE"


# ==================== Data Classes ====================


@dataclass
class ObjectMetadata:
    """Metadata for a stored object."""

    key: str
    size: int = 0
    content_type: str = "application/octet-stream"
    etag: str = ""
    last_modified: Optional[datetime] = None
    storage_class: StorageClass = StorageClass.STANDARD
    custom_metadata: dict[str, str] = field(default_factory=dict)
    # CoPaw extension fields
    tenant_id: str = ""
    owner_id: str = ""
    category: str = ""  # workspace/skill/memory/media/model/config/other


@dataclass
class ListResult:
    """Result of a list_objects call."""

    objects: list[ObjectMetadata] = field(default_factory=list)
    prefix: str = ""
    is_truncated: bool = False
    continuation_token: str = ""


# ==================== Exceptions ====================


class StorageError(AgentRuntimeErrorException):
    """Base exception for all storage errors."""

    def __init__(
        self,
        message: str,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__("STORAGE_ERROR", message, details)


class StorageNotFoundError(StorageError):
    """Raised when a requested object does not exist."""

    def __init__(
        self,
        key: str,
        details: Optional[dict] = None,
    ) -> None:
        if details is None:
            details = {}
        details["key"] = key
        super().__init__(f"Object not found: {key}", details)
        self.key = key


class StoragePermissionError(StorageError):
    """Raised when access to an object is denied."""

    def __init__(
        self,
        key: str,
        reason: str = "permission denied",
        details: Optional[dict] = None,
    ) -> None:
        if details is None:
            details = {}
        details["key"] = key
        super().__init__(f"Access denied for {key}: {reason}", details)
        self.key = key


class StorageTimeoutError(StorageError):
    """Raised when a storage operation times out."""

    def __init__(
        self,
        key: str,
        timeout: float = 0,
        details: Optional[dict] = None,
    ) -> None:
        if details is None:
            details = {}
        details["key"] = key
        details["timeout"] = timeout
        super().__init__(
            f"Storage operation timed out for {key} after {timeout}s",
            details,
        )
        self.key = key
        self.timeout = timeout


class StorageConflictError(StorageError):
    """Raised when a concurrent write conflict occurs."""

    def __init__(
        self,
        key: str,
        details: Optional[dict] = None,
    ) -> None:
        if details is None:
            details = {}
        details["key"] = key
        super().__init__(f"Write conflict for {key}", details)
        self.key = key


# ==================== Abstract Provider ====================


class ObjectStorageProvider(abc.ABC):
    """Unified object storage interface.

    All storage backends (FileSystem, S3, MinIO, OSS, SFTP) must
    implement this interface so that upper-layer code can switch
    backends purely through configuration.
    """

    # -- Basic Operations -------------------------------------------------- #

    @abc.abstractmethod
    async def put(
        self,
        key: str,
        data: bytes | AsyncIterator[bytes],
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
        storage_class: StorageClass = StorageClass.STANDARD,
    ) -> ObjectMetadata:
        """Upload an object."""

    @abc.abstractmethod
    async def get(self, key: str) -> bytes:
        """Download an object (full content)."""

    @abc.abstractmethod
    async def get_stream(self, key: str) -> AsyncIterator[bytes]:
        """Stream-download an object (for large files)."""

    @abc.abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete an object.  Returns True if the object existed."""

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        """Check whether an object exists."""

    @abc.abstractmethod
    async def copy(self, source_key: str, dest_key: str) -> ObjectMetadata:
        """Copy an object within the same bucket."""

    # -- Listing ----------------------------------------------------------- #

    @abc.abstractmethod
    async def list_objects(
        self,
        prefix: str,
        delimiter: str = "/",
        max_keys: int = 1000,
        continuation_token: str = "",
    ) -> ListResult:
        """List objects under a given prefix."""

    # -- Metadata ---------------------------------------------------------- #

    @abc.abstractmethod
    async def get_metadata(self, key: str) -> ObjectMetadata:
        """Retrieve metadata for an object."""

    @abc.abstractmethod
    async def put_metadata(
        self,
        key: str,
        metadata: dict[str, str],
    ) -> ObjectMetadata:
        """Update custom metadata for an existing object."""

    # -- Pre-signed URLs --------------------------------------------------- #

    @abc.abstractmethod
    async def presign_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a pre-signed URL for temporary access."""

    # -- Lifecycle --------------------------------------------------------- #

    async def initialize(self) -> None:
        """Initialize the storage backend (open connections, etc.)."""

    async def close(self) -> None:
        """Release resources held by the storage backend."""
