# -*- coding: utf-8 -*-
"""
FileSystem storage adapter — fully compatible with personal edition ``~/.copaw/``.

The ``key`` is mapped to a relative path under ``base_dir``.  Metadata is
stored as a ``.meta.json`` sidecar file next to the original file.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import AsyncIterator, Optional

import aiofiles
import aiofiles.os

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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FileSystemStorageAdapter(ObjectStorageProvider):
    """Local filesystem storage adapter.

    Fully compatible with the personal-edition ``~/.copaw/`` layout.
    The ``key`` maps directly to a relative path under ``base_dir``.
    """

    def __init__(self, config: StorageConfig) -> None:
        self._base_dir = Path(config.filesystem_base_dir).expanduser().resolve()
        self._config = config

    # -- Internal helpers -------------------------------------------------- #

    def _resolve(self, key: str) -> Path:
        """Resolve a storage key to an absolute filesystem path."""
        # Prevent path traversal outside base_dir
        resolved = (self._base_dir / key).resolve()
        if not str(resolved).startswith(str(self._base_dir)):
            raise StoragePermissionError(
                key, reason="path traversal outside base_dir"
            )
        return resolved

    def _meta_path(self, file_path: Path) -> Path:
        """Return the path to the sidecar .meta.json file."""
        return file_path.with_suffix(file_path.suffix + ".meta.json")

    def _read_meta(self, key: str) -> dict:
        """Read sidecar metadata (if it exists)."""
        mp = self._meta_path(self._resolve(key))
        if mp.exists():
            try:
                return json.loads(mp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _write_meta(self, key: str, metadata: dict) -> None:
        """Write sidecar metadata."""
        mp = self._meta_path(self._resolve(key))
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    def _stat_to_metadata(self, key: str, path: Path) -> ObjectMetadata:
        """Convert a file's stat info into ObjectMetadata."""
        try:
            st = path.stat()
        except OSError:
            raise StorageNotFoundError(key)

        meta = self._read_meta(key)
        lm = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)

        return ObjectMetadata(
            key=key,
            size=st.st_size,
            content_type=meta.get("content_type", "application/octet-stream"),
            etag=meta.get("etag", hashlib.md5(key.encode()).hexdigest()),
            last_modified=lm,
            storage_class=StorageClass(meta.get("storage_class", "STANDARD")),
            custom_metadata=meta.get("custom_metadata", {}),
            tenant_id=meta.get("tenant_id", ""),
            owner_id=meta.get("owner_id", ""),
            category=meta.get("category", ""),
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
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, (bytes, bytearray)):
            async with aiofiles.open(path, "wb") as f:
                await f.write(data)
        else:
            async with aiofiles.open(path, "wb") as f:
                async for chunk in data:
                    await f.write(chunk)

        # Compute content hash for etag
        file_bytes = path.read_bytes()
        etag = hashlib.md5(file_bytes).hexdigest()

        # Write sidecar metadata
        meta: dict = {
            "content_type": content_type,
            "storage_class": storage_class.value,
            "etag": etag,
            "custom_metadata": metadata or {},
        }
        self._write_meta(key, meta)

        return self._stat_to_metadata(key, path)

    async def get(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise StorageNotFoundError(key)
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def get_stream(self, key: str) -> AsyncIterator[bytes]:
        path = self._resolve(key)
        if not path.exists():
            raise StorageNotFoundError(key)
        chunk_size = 64 * 1024  # 64 KB
        async with aiofiles.open(path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    async def delete(self, key: str) -> bool:
        path = self._resolve(key)
        if not path.exists():
            return False
        path.unlink()
        # Also clean up sidecar metadata
        mp = self._meta_path(path)
        if mp.exists():
            mp.unlink()
        return True

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    async def copy(self, source_key: str, dest_key: str) -> ObjectMetadata:
        src = self._resolve(source_key)
        dst = self._resolve(dest_key)
        if not src.exists():
            raise StorageNotFoundError(source_key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        # Copy sidecar metadata too
        src_meta = self._meta_path(src)
        if src_meta.exists():
            dst_meta = self._meta_path(dst)
            shutil.copy2(str(src_meta), str(dst_meta))
        return self._stat_to_metadata(dest_key, dst)

    # -- Listing ----------------------------------------------------------- #

    async def list_objects(
        self,
        prefix: str,
        delimiter: str = "/",
        max_keys: int = 1000,
        continuation_token: str = "",
    ) -> ListResult:
        base = self._resolve(prefix)
        if not base.exists() or not base.is_dir():
            return ListResult(prefix=prefix)

        objects: list[ObjectMetadata] = []
        count = 0
        # Use continuation_token as a skip count for simplicity
        skip = int(continuation_token) if continuation_token.isdigit() else 0

        for root, _dirs, files in os.walk(str(base)):
            for fname in files:
                # Skip sidecar metadata files
                if fname.endswith(".meta.json"):
                    continue
                if count < skip:
                    count += 1
                    continue
                fpath = Path(root) / fname
                rel_key = str(fpath.relative_to(self._base_dir)).replace(os.sep, "/")
                try:
                    objects.append(self._stat_to_metadata(rel_key, fpath))
                except StorageNotFoundError:
                    continue
                count += 1
                if len(objects) >= max_keys:
                    return ListResult(
                        objects=objects,
                        prefix=prefix,
                        is_truncated=True,
                        continuation_token=str(count),
                    )

        return ListResult(objects=objects, prefix=prefix)

    # -- Metadata ---------------------------------------------------------- #

    async def get_metadata(self, key: str) -> ObjectMetadata:
        path = self._resolve(key)
        return self._stat_to_metadata(key, path)

    async def put_metadata(
        self,
        key: str,
        metadata: dict[str, str],
    ) -> ObjectMetadata:
        path = self._resolve(key)
        if not path.exists():
            raise StorageNotFoundError(key)
        existing = self._read_meta(key)
        existing.setdefault("custom_metadata", {}).update(metadata)
        self._write_meta(key, existing)
        return self._stat_to_metadata(key, path)

    # -- Pre-signed URLs --------------------------------------------------- #

    async def presign_url(self, key: str, expires_in: int = 3600) -> str:
        """FileSystem adapter returns a ``file:///`` URL.

        This is a no-op for personal edition — the file is locally accessible.
        """
        path = self._resolve(key)
        if not path.exists():
            raise StorageNotFoundError(key)
        return path.as_uri()
