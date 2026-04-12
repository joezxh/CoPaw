# -*- coding: utf-8 -*-
"""
MinIO storage adapter.

MinIO is fully S3-compatible, so this adapter could delegate to
S3StorageAdapter.  However, the MinIO native SDK (miniopy-async)
offers some optimised paths, so we provide a dedicated adapter.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

from .base import (
    ListResult,
    ObjectMetadata,
    ObjectStorageProvider,
    StorageClass,
    StorageNotFoundError,
    StoragePermissionError,
)
from .config import StorageConfig


class MinIOStorageAdapter(ObjectStorageProvider):
    """MinIO adapter using the miniopy-async native SDK."""

    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        self._bucket = config.effective_bucket()
        self._client = None

    async def initialize(self) -> None:
        try:
            from miniopy_async import Minio
        except ImportError:
            raise ImportError(
                "miniopy-async is required for MinIO storage backend. "
                "Install it with: pip install copaw[enterprise]"
            )

        self._client = Minio(
            endpoint=self._config.minio_endpoint,
            access_key=self._config.minio_access_key,
            secret_key=self._config.minio_secret_key,
            secure=self._config.minio_secure,
        )
        # Ensure bucket exists
        if not await self._client.bucket_exists(self._bucket):
            await self._client.make_bucket(self._bucket)

    async def close(self) -> None:
        self._client = None

    # -- Internal helpers -------------------------------------------------- #

    def _minio_obj_to_metadata(self, obj, key: str) -> ObjectMetadata:
        """Convert a MinIO object to ObjectMetadata."""
        return ObjectMetadata(
            key=key,
            size=obj.size if hasattr(obj, "size") else 0,
            content_type=getattr(obj, "content_type", "application/octet-stream"),
            etag=getattr(obj, "etag", "").strip('"'),
            last_modified=getattr(obj, "last_modified", None),
            storage_class=StorageClass.STANDARD,
        )

    # -- Basic Operations -------------------------------------------------- #

    async def put(
        self,
        key: str,
        data: bytes | AsyncIterator[bytes],
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
        storage_class: StorageClass = StorageClass.STANDARD,
    ) -> ObjectMetadata:
        if isinstance(data, (bytes, bytearray)):
            from io import BytesIO
            stream = BytesIO(data)
            length = len(data)
        else:
            # Materialize async iterator
            chunks: list[bytes] = []
            async for chunk in data:
                chunks.append(chunk)
            combined = b"".join(chunks)
            from io import BytesIO
            stream = BytesIO(combined)
            length = len(combined)

        await self._client.put_object(
            bucket_name=self._bucket,
            object_name=key,
            data=stream,
            length=length,
            content_type=content_type,
            metadata=metadata,
        )
        return await self.get_metadata(key)

    async def get(self, key: str) -> bytes:
        try:
            resp = await self._client.get_object(
                bucket_name=self._bucket,
                object_name=key,
            )
            data = await resp.read()
            resp.close()
            resp.release()
            return data
        except Exception as exc:
            if "NoSuchKey" in str(exc) or "does not exist" in str(exc):
                raise StorageNotFoundError(key)
            raise

    async def get_stream(self, key: str) -> AsyncIterator[bytes]:
        try:
            resp = await self._client.get_object(
                bucket_name=self._bucket,
                object_name=key,
            )
            while True:
                chunk = await resp.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
            resp.close()
            resp.release()
        except StorageNotFoundError:
            raise
        except Exception as exc:
            if "NoSuchKey" in str(exc) or "does not exist" in str(exc):
                raise StorageNotFoundError(key)
            raise

    async def delete(self, key: str) -> bool:
        try:
            await self._client.remove_object(
                bucket_name=self._bucket,
                object_name=key,
            )
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        try:
            await self._client.stat_object(
                bucket_name=self._bucket,
                object_name=key,
            )
            return True
        except Exception:
            return False

    async def copy(self, source_key: str, dest_key: str) -> ObjectMetadata:
        from miniopy_async.commonconfig import CopySource
        await self._client.copy_object(
            bucket_name=self._bucket,
            object_name=dest_key,
            source=CopySource(self._bucket, source_key),
        )
        return await self.get_metadata(dest_key)

    # -- Listing ----------------------------------------------------------- #

    async def list_objects(
        self,
        prefix: str,
        delimiter: str = "/",
        max_keys: int = 1000,
        continuation_token: str = "",
    ) -> ListResult:
        objects: list[ObjectMetadata] = []
        async for obj in self._client.list_objects(
            bucket_name=self._bucket,
            prefix=prefix,
            recursive=(delimiter != "/"),
        ):
            if obj.is_dir:
                continue
            objects.append(
                ObjectMetadata(
                    key=obj.object_name,
                    size=obj.size if hasattr(obj, "size") else 0,
                    etag=getattr(obj, "etag", "").strip('"'),
                    last_modified=getattr(obj, "last_modified", None),
                    storage_class=StorageClass.STANDARD,
                )
            )
            if len(objects) >= max_keys:
                break
        return ListResult(objects=objects, prefix=prefix)

    # -- Metadata ---------------------------------------------------------- #

    async def get_metadata(self, key: str) -> ObjectMetadata:
        try:
            obj = await self._client.stat_object(
                bucket_name=self._bucket,
                object_name=key,
            )
        except Exception as exc:
            if "does not exist" in str(exc) or "NoSuchKey" in str(exc):
                raise StorageNotFoundError(key)
            raise

        return ObjectMetadata(
            key=key,
            size=obj.size if hasattr(obj, "size") else 0,
            content_type=getattr(obj, "content_type", "application/octet-stream"),
            etag=getattr(obj, "etag", "").strip('"'),
            last_modified=getattr(obj, "last_modified", None),
            storage_class=StorageClass.STANDARD,
            custom_metadata=getattr(obj, "metadata", {}) or {},
        )

    async def put_metadata(
        self,
        key: str,
        metadata: dict[str, str],
    ) -> ObjectMetadata:
        """Update metadata by copying the object onto itself."""
        from miniopy_async.commonconfig import CopySource
        current = await self.get_metadata(key)
        merged = {**current.custom_metadata, **metadata}
        await self._client.copy_object(
            bucket_name=self._bucket,
            object_name=key,
            source=CopySource(self._bucket, key),
            metadata=merged,
        )
        return await self.get_metadata(key)

    # -- Pre-signed URLs --------------------------------------------------- #

    async def presign_url(self, key: str, expires_in: int = 3600) -> str:
        if not self._config.presign_enabled:
            raise StoragePermissionError(
                key, reason="pre-signed URLs are disabled in configuration"
            )
        from datetime import timedelta
        return await self._client.presigned_get_object(
            bucket_name=self._bucket,
            object_name=key,
            expires=timedelta(seconds=expires_in),
        )
