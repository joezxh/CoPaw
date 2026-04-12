# -*- coding: utf-8 -*-
"""
SFTP storage adapter.

Simulates object-storage key-value semantics over SFTP.
The ``key`` maps to a relative path under ``base_dir`` on the SFTP server.
"""
from __future__ import annotations

import hashlib
import os
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


class SFTPStorageAdapter(ObjectStorageProvider):
    """SFTP adapter for traditional file servers and internal NAS.

    Simulates object-storage semantics over SFTP.  The ``key`` maps
    to a relative path under ``base_dir`` on the remote server.
    """

    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        self._base_dir = config.sftp_base_dir
        self._conn = None
        self._sftp = None

    async def initialize(self) -> None:
        try:
            import asyncssh
        except ImportError:
            raise ImportError(
                "asyncssh is required for SFTP storage backend. "
                "Install it with: pip install copaw[enterprise]"
            )

        connect_kwargs: dict = {
            "host": self._config.sftp_host,
            "port": self._config.sftp_port,
            "username": self._config.sftp_username,
        }
        if self._config.sftp_password:
            connect_kwargs["password"] = self._config.sftp_password
        if self._config.sftp_private_key_path:
            connect_kwargs["client_keys"] = [self._config.sftp_private_key_path]

        self._conn = await asyncssh.connect(**connect_kwargs)
        self._sftp = await self._conn.start_sftp_client()

        # Ensure base directory exists
        try:
            await self._sftp.mkdir(self._base_dir, exist_ok=True)
        except Exception:
            pass

    async def close(self) -> None:
        if self._sftp:
            self._sftp.exit()
            self._sftp = None
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
            self._conn = None

    # -- Internal helpers -------------------------------------------------- #

    def _remote_path(self, key: str) -> str:
        """Build the absolute remote path from a storage key."""
        return os.path.join(self._base_dir, key).replace("\\", "/")

    # -- Basic Operations -------------------------------------------------- #

    async def put(
        self,
        key: str,
        data: bytes | AsyncIterator[bytes],
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
        storage_class: StorageClass = StorageClass.STANDARD,
    ) -> ObjectMetadata:
        remote = self._remote_path(key)

        # Ensure parent directory exists
        parent = os.path.dirname(remote)
        try:
            await self._sftp.mkdir(parent, exist_ok=True)
        except Exception:
            pass

        if isinstance(data, (bytes, bytearray)):
            from io import BytesIO
            await self._sftp.putfo(BytesIO(data), remote)
        else:
            # Materialize stream
            chunks: list[bytes] = []
            async for chunk in data:
                chunks.append(chunk)
            from io import BytesIO
            await self._sftp.putfo(BytesIO(b"".join(chunks)), remote)

        return await self.get_metadata(key)

    async def get(self, key: str) -> bytes:
        remote = self._remote_path(key)
        try:
            from io import BytesIO
            buf = BytesIO()
            await self._sftp.getfo(remote, buf)
            return buf.getvalue()
        except Exception as exc:
            if "No such file" in str(exc) or "does not exist" in str(exc):
                raise StorageNotFoundError(key)
            raise

    async def get_stream(self, key: str) -> AsyncIterator[bytes]:
        data = await self.get(key)
        chunk_size = 64 * 1024
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    async def delete(self, key: str) -> bool:
        remote = self._remote_path(key)
        try:
            await self._sftp.remove(remote)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        remote = self._remote_path(key)
        try:
            await self._sftp.stat(remote)
            return True
        except Exception:
            return False

    async def copy(self, source_key: str, dest_key: str) -> ObjectMetadata:
        # SFTP doesn't have a native copy — download then upload
        data = await self.get(source_key)
        return await self.put(dest_key, data)

    # -- Listing ----------------------------------------------------------- #

    async def list_objects(
        self,
        prefix: str,
        delimiter: str = "/",
        max_keys: int = 1000,
        continuation_token: str = "",
    ) -> ListResult:
        remote_prefix = self._remote_path(prefix)
        objects: list[ObjectMetadata] = []

        async def _walk(dir_path: str, key_prefix: str) -> None:
            try:
                entries = await self._sftp.readdir(dir_path)
            except Exception:
                return
            for entry in entries:
                name = entry.filename
                if name in (".", ".."):
                    continue
                entry_key = f"{key_prefix}{name}"
                full_path = os.path.join(dir_path, name).replace("\\", "/")
                if entry.attrs and entry.attrs.type == 2:  # directory
                    if delimiter == "/":
                        continue  # don't recurse
                    await _walk(full_path, f"{entry_key}/")
                else:
                    try:
                        stat = await self._sftp.stat(full_path)
                        objects.append(
                            ObjectMetadata(
                                key=entry_key,
                                size=getattr(stat, "size", 0) or 0,
                                last_modified=getattr(stat, "mtime", None),
                                storage_class=StorageClass.STANDARD,
                            )
                        )
                    except Exception:
                        pass
                if len(objects) >= max_keys:
                    return

        await _walk(remote_prefix, prefix)
        return ListResult(objects=objects, prefix=prefix)

    # -- Metadata ---------------------------------------------------------- #

    async def get_metadata(self, key: str) -> ObjectMetadata:
        remote = self._remote_path(key)
        try:
            stat = await self._sftp.stat(remote)
        except Exception as exc:
            if "No such file" in str(exc) or "does not exist" in str(exc):
                raise StorageNotFoundError(key)
            raise

        lm = None
        mtime = getattr(stat, "mtime", None)
        if mtime:
            from datetime import datetime as dt
            lm = dt.fromtimestamp(mtime, tz=timezone.utc)

        return ObjectMetadata(
            key=key,
            size=getattr(stat, "size", 0) or 0,
            content_type="application/octet-stream",
            last_modified=lm,
            storage_class=StorageClass.STANDARD,
        )

    async def put_metadata(
        self,
        key: str,
        metadata: dict[str, str],
    ) -> ObjectMetadata:
        """SFTP does not support native metadata — best-effort no-op."""
        return await self.get_metadata(key)

    # -- Pre-signed URLs --------------------------------------------------- #

    async def presign_url(self, key: str, expires_in: int = 3600) -> str:
        """SFTP does not support pre-signed URLs."""
        raise StoragePermissionError(
            key, reason="SFTP adapter does not support pre-signed URLs"
        )
