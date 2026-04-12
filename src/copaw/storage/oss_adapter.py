# -*- coding: utf-8 -*-
"""
Alibaba Cloud OSS storage adapter.

Uses the ``oss2`` SDK.  Note that ``oss2`` is synchronous, so we wrap
calls via ``asyncio.to_thread`` for async compatibility.
"""
from __future__ import annotations

import asyncio
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


class OSSStorageAdapter(ObjectStorageProvider):
    """Alibaba Cloud OSS adapter using the oss2 SDK."""

    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        self._bucket_name = config.effective_bucket()
        self._bucket = None
        self._auth = None

    async def initialize(self) -> None:
        try:
            import oss2
        except ImportError:
            raise ImportError(
                "oss2 is required for OSS storage backend. "
                "Install it with: pip install copaw[enterprise]"
            )

        self._auth = oss2.Auth(
            self._config.oss_access_key_id,
            self._config.oss_access_key_secret,
        )
        self._bucket = oss2.Bucket(
            self._auth,
            self._config.oss_endpoint,
            self._bucket_name,
        )
        # Ensure bucket exists
        try:
            if not await asyncio.to_thread(self._bucket.exists):
                raise RuntimeError(
                    f"OSS bucket '{self._bucket_name}' does not exist"
                )
        except oss2.exceptions.NoSuchBucket:
            raise RuntimeError(
                f"OSS bucket '{self._bucket_name}' does not exist. "
                "Please create it manually first."
            )

    async def close(self) -> None:
        self._bucket = None

    # -- Basic Operations -------------------------------------------------- #

    async def put(
        self,
        key: str,
        data: bytes | AsyncIterator[bytes],
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
        storage_class: StorageClass = StorageClass.STANDARD,
    ) -> ObjectMetadata:
        if not isinstance(data, (bytes, bytearray)):
            chunks: list[bytes] = []
            async for chunk in data:
                chunks.append(chunk)
            data = b"".join(chunks)

        headers: dict = {}
        if metadata:
            for k, v in metadata.items():
                headers[f"x-oss-meta-{k}"] = v

        await asyncio.to_thread(
            self._bucket.put_object,
            key,
            data,
            headers=headers,
        )
        return await self.get_metadata(key)

    async def get(self, key: str) -> bytes:
        try:
            result = await asyncio.to_thread(
                self._bucket.get_object, key
            )
            return await asyncio.to_thread(result.read)
        except Exception as exc:
            if "NoSuchKey" in str(exc) or "does not exist" in str(exc):
                raise StorageNotFoundError(key)
            raise

    async def get_stream(self, key: str) -> AsyncIterator[bytes]:
        data = await self.get(key)
        chunk_size = 64 * 1024
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    async def delete(self, key: str) -> bool:
        try:
            await asyncio.to_thread(self._bucket.delete_object, key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        try:
            return await asyncio.to_thread(self._bucket.object_exists, key)
        except Exception:
            return False

    async def copy(self, source_key: str, dest_key: str) -> ObjectMetadata:
        await asyncio.to_thread(
            self._bucket.copy_object,
            self._bucket_name,
            source_key,
            dest_key,
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
        marker = continuation_token

        import oss2 as _oss2

        def _list():
            return list(
                _oss2.ObjectIterator(
                    self._bucket,
                    prefix=prefix,
                    delimiter=delimiter,
                    max_keys=max_keys,
                    marker=marker,
                )
            )

        items = await asyncio.to_thread(_list)
        for obj in items:
            if obj.is_prefix():
                continue
            objects.append(
                ObjectMetadata(
                    key=obj.key,
                    size=obj.size,
                    etag=getattr(obj, "etag", "").strip('"'),
                    last_modified=getattr(obj, "last_modified", None),
                    storage_class=StorageClass.STANDARD,
                )
            )
        is_truncated = len(items) >= max_keys
        next_marker = items[-1].key if items and is_truncated else ""
        return ListResult(
            objects=objects,
            prefix=prefix,
            is_truncated=is_truncated,
            continuation_token=next_marker,
        )

    # -- Metadata ---------------------------------------------------------- #

    async def get_metadata(self, key: str) -> ObjectMetadata:
        try:
            info = await asyncio.to_thread(
                self._bucket.head_object, key
            )
        except Exception as exc:
            if "NoSuchKey" in str(exc) or "does not exist" in str(exc):
                raise StorageNotFoundError(key)
            raise

        lm = getattr(info, "last_modified", None)
        custom_meta = {}
        for k, v in getattr(info, "headers", {}).items():
            if k.startswith("x-oss-meta-"):
                custom_meta[k[len("x-oss-meta-"):]] = v

        return ObjectMetadata(
            key=key,
            size=getattr(info, "content_length", 0),
            content_type=getattr(info, "content_type", "application/octet-stream"),
            etag=getattr(info, "etag", "").strip('"'),
            last_modified=lm,
            storage_class=StorageClass.STANDARD,
            custom_metadata=custom_meta,
        )

    async def put_metadata(
        self,
        key: str,
        metadata: dict[str, str],
    ) -> ObjectMetadata:
        """Update metadata by copying the object onto itself."""
        await asyncio.to_thread(
            self._bucket.copy_object,
            self._bucket_name,
            key,
            key,
            headers={f"x-oss-meta-{k}": v for k, v in metadata.items()},
        )
        return await self.get_metadata(key)

    # -- Pre-signed URLs --------------------------------------------------- #

    async def presign_url(self, key: str, expires_in: int = 3600) -> str:
        if not self._config.presign_enabled:
            raise StoragePermissionError(
                key, reason="pre-signed URLs are disabled in configuration"
            )
        return await asyncio.to_thread(
            self._bucket.sign_url,
            "GET",
            key,
            expires_in,
        )
