# -*- coding: utf-8 -*-
"""
AWS S3 / S3-compatible storage adapter.

Supports AWS S3, Ceph, DigitalOcean Spaces, and any S3-compatible storage.
Uses ``aioboto3`` for async operations.
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
    StorageTimeoutError,
)
from .config import StorageConfig


class S3StorageAdapter(ObjectStorageProvider):
    """AWS S3 / S3-compatible protocol adapter.

    Supports: AWS S3, Ceph, DigitalOcean Spaces, and any S3-compatible storage.
    """

    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        self._bucket = config.effective_bucket()
        self._session = None
        self._client = None
        self._resource = None

    async def initialize(self) -> None:
        """Create the async S3 client."""
        try:
            import aioboto3
        except ImportError:
            raise ImportError(
                "aioboto3 is required for S3 storage backend. "
                "Install it with: pip install copaw[enterprise]"
            )

        self._session = aioboto3.Session()
        kwargs: dict = {
            "aws_access_key_id": self._config.s3_access_key or None,
            "aws_secret_access_key": self._config.s3_secret_key or None,
            "region_name": self._config.s3_region or "us-east-1",
        }
        if self._config.s3_endpoint_url:
            kwargs["endpoint_url"] = self._config.s3_endpoint_url

        self._client = await self._session.client("s3", **kwargs).__aenter__()

        # Ensure bucket exists
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except Exception:
            try:
                await self._client.create_bucket(Bucket=self._bucket)
            except Exception:
                pass  # Bucket may already exist (race condition)

    async def close(self) -> None:
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    # -- Internal helpers -------------------------------------------------- #

    def _s3_object_to_metadata(self, obj: dict) -> ObjectMetadata:
        """Convert an S3 list-object entry to ObjectMetadata."""
        lm = obj.get("LastModified")
        if lm and hasattr(lm, "replace"):
            lm = lm.replace(tzinfo=timezone.utc) if lm.tzinfo is None else lm
        return ObjectMetadata(
            key=obj.get("Key", ""),
            size=obj.get("Size", 0),
            content_type="application/octet-stream",
            etag=obj.get("ETag", "").strip('"'),
            last_modified=lm,
            storage_class=StorageClass(obj.get("StorageClass", "STANDARD")),
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
        extra_args: dict = {
            "ContentType": content_type,
            "StorageClass": storage_class.value,
        }
        if metadata:
            extra_args["Metadata"] = metadata

        body: bytes | AsyncIterator[bytes]
        if isinstance(data, (bytes, bytearray)):
            body = data
        else:
            # Materialize stream for S3 put_object
            chunks: list[bytes] = []
            async for chunk in data:
                chunks.append(chunk)
            body = b"".join(chunks)

        await self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            **extra_args,
        )
        return await self.get_metadata(key)

    async def get(self, key: str) -> bytes:
        try:
            resp = await self._client.get_object(
                Bucket=self._bucket, Key=key
            )
            return await resp["Body"].read()
        except self._client.exceptions.NoSuchKey:
            raise StorageNotFoundError(key)
        except Exception as exc:
            if "NoSuchKey" in str(exc) or "404" in str(exc):
                raise StorageNotFoundError(key)
            raise

    async def get_stream(self, key: str) -> AsyncIterator[bytes]:
        try:
            resp = await self._client.get_object(
                Bucket=self._bucket, Key=key
            )
            async for chunk in resp["Body"].iter_chunks(64 * 1024):
                yield chunk
        except Exception as exc:
            if "NoSuchKey" in str(exc) or "404" in str(exc):
                raise StorageNotFoundError(key)
            raise

    async def delete(self, key: str) -> bool:
        try:
            await self._client.delete_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        try:
            await self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    async def copy(self, source_key: str, dest_key: str) -> ObjectMetadata:
        copy_source = {"Bucket": self._bucket, "Key": source_key}
        await self._client.copy_object(
            CopySource=copy_source,
            Bucket=self._bucket,
            Key=dest_key,
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
        kwargs: dict = {
            "Bucket": self._bucket,
            "Prefix": prefix,
            "Delimiter": delimiter,
            "MaxKeys": max_keys,
        }
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        resp = await self._client.list_objects_v2(**kwargs)
        objects = [
            self._s3_object_to_metadata(obj)
            for obj in resp.get("Contents", [])
        ]
        return ListResult(
            objects=objects,
            prefix=prefix,
            is_truncated=resp.get("IsTruncated", False),
            continuation_token=resp.get("NextContinuationToken", ""),
        )

    # -- Metadata ---------------------------------------------------------- #

    async def get_metadata(self, key: str) -> ObjectMetadata:
        try:
            resp = await self._client.head_object(
                Bucket=self._bucket, Key=key
            )
        except Exception as exc:
            if "404" in str(exc) or "Not Found" in str(exc):
                raise StorageNotFoundError(key)
            raise

        lm = resp.get("LastModified")
        if lm and hasattr(lm, "replace"):
            lm = lm.replace(tzinfo=timezone.utc) if lm.tzinfo is None else lm

        return ObjectMetadata(
            key=key,
            size=resp.get("ContentLength", 0),
            content_type=resp.get("ContentType", "application/octet-stream"),
            etag=resp.get("ETag", "").strip('"'),
            last_modified=lm,
            storage_class=StorageClass(resp.get("StorageClass", "STANDARD")),
            custom_metadata=resp.get("Metadata", {}),
        )

    async def put_metadata(
        self,
        key: str,
        metadata: dict[str, str],
    ) -> ObjectMetadata:
        """Update custom metadata by copying the object onto itself."""
        copy_source = {"Bucket": self._bucket, "Key": key}
        current = await self.get_metadata(key)
        merged = {**current.custom_metadata, **metadata}
        await self._client.copy_object(
            CopySource=copy_source,
            Bucket=self._bucket,
            Key=key,
            Metadata=merged,
            MetadataDirective="REPLACE",
        )
        return await self.get_metadata(key)

    # -- Pre-signed URLs --------------------------------------------------- #

    async def presign_url(self, key: str, expires_in: int = 3600) -> str:
        if not self._config.presign_enabled:
            raise StoragePermissionError(
                key, reason="pre-signed URLs are disabled in configuration"
            )
        return await self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
