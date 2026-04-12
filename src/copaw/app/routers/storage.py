# -*- coding: utf-8 -*-
"""
Object storage REST API routes.

Provides CRUD operations for the unified object storage layer.
All endpoints require enterprise authentication.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query
from pydantic import BaseModel, Field

from ...storage.base import StorageNotFoundError, StoragePermissionError, StorageError
from ...storage.config import StorageConfig


router = APIRouter(prefix="/enterprise/storage", tags=["Enterprise Storage"])


# -- Dependency ----------------------------------------------------------- #


def _get_storage(request: Request):
    """Retrieve the storage provider from app state."""
    storage = getattr(request.app.state, "storage", None)
    if storage is None:
        raise HTTPException(
            status_code=503,
            detail="Object storage is not configured or not initialized",
        )
    return storage


# -- Request / Response schemas ------------------------------------------- #


class StorageUploadResponse(BaseModel):
    key: str
    size: int
    etag: str = ""
    content_type: str = ""


class StorageListResponse(BaseModel):
    objects: list[dict]
    prefix: str
    is_truncated: bool = False
    continuation_token: str = ""


class StorageMetadataResponse(BaseModel):
    key: str
    size: int = 0
    content_type: str = ""
    etag: str = ""
    last_modified: Optional[str] = None
    storage_class: str = "STANDARD"
    custom_metadata: dict = {}


class StorageStatsResponse(BaseModel):
    backend: str = ""
    bucket: str = ""
    presign_enabled: bool = True


class PresignUrlResponse(BaseModel):
    url: str
    expires_in: int


# -- Endpoints ------------------------------------------------------------ #
# NOTE: Specific routes (list, stats, presign, metadata) MUST come before
# the catch-all /{key:path} routes, otherwise they'll be swallowed.


@router.get("/list", response_model=StorageListResponse)
async def list_objects(
    prefix: str = Query("", description="Object key prefix"),
    delimiter: str = Query("/", description="Delimiter for grouping"),
    max_keys: int = Query(1000, ge=1, le=10000),
    continuation_token: str = Query("", description="Pagination token"),
    storage=Depends(_get_storage),
):
    """List objects under a given prefix."""
    result = await storage.list_objects(
        prefix=prefix,
        delimiter=delimiter,
        max_keys=max_keys,
        continuation_token=continuation_token,
    )
    return StorageListResponse(
        objects=[
            {
                "key": o.key,
                "size": o.size,
                "etag": o.etag,
                "last_modified": o.last_modified.isoformat() if o.last_modified else None,
                "storage_class": o.storage_class.value,
            }
            for o in result.objects
        ],
        prefix=result.prefix,
        is_truncated=result.is_truncated,
        continuation_token=result.continuation_token,
    )


@router.get("/stats", response_model=StorageStatsResponse)
async def get_storage_stats(
    request: Request,
):
    """Get storage backend configuration and stats."""
    storage = getattr(request.app.state, "storage", None)
    cfg = None
    _cfg_obj = getattr(request.app.state, "config_obj", None)
    if _cfg_obj is not None:
        cfg = getattr(_cfg_obj.enterprise, "storage", None)
    if cfg is None:
        # Try to build default config
        from ...storage.config import StorageConfig
        cfg = StorageConfig()

    return StorageStatsResponse(
        backend=cfg.backend,
        bucket=cfg.effective_bucket(),
        presign_enabled=cfg.presign_enabled,
    )


@router.get("/presign/{key:path}", response_model=PresignUrlResponse)
async def get_presigned_url(
    key: str,
    expires_in: int = Query(3600, ge=60, le=86400),
    storage=Depends(_get_storage),
):
    """Generate a pre-signed URL for temporary access."""
    try:
        url = await storage.presign_url(key, expires_in=expires_in)
        return PresignUrlResponse(url=url, expires_in=expires_in)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail=f"Object not found: {key}")
    except StoragePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/metadata/{key:path}", response_model=StorageMetadataResponse)
async def get_object_metadata(
    key: str,
    storage=Depends(_get_storage),
):
    """Get metadata for an object."""
    try:
        meta = await storage.get_metadata(key)
        return StorageMetadataResponse(
            key=meta.key,
            size=meta.size,
            content_type=meta.content_type,
            etag=meta.etag,
            last_modified=meta.last_modified.isoformat() if meta.last_modified else None,
            storage_class=meta.storage_class.value,
            custom_metadata=meta.custom_metadata,
        )
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail=f"Object not found: {key}")
    except StoragePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.put("/{key:path}", response_model=StorageUploadResponse)
async def upload_object(
    key: str,
    file: UploadFile = File(...),
    storage=Depends(_get_storage),
):
    """Upload a file to object storage."""
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"
    try:
        meta = await storage.put(key, content, content_type=content_type)
        return StorageUploadResponse(
            key=meta.key,
            size=meta.size,
            etag=meta.etag,
            content_type=meta.content_type,
        )
    except StoragePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{key:path}")
async def download_object(
    key: str,
    storage=Depends(_get_storage),
):
    """Download a file from object storage."""
    try:
        data = await storage.get(key)
        meta = await storage.get_metadata(key)
        from fastapi.responses import Response
        return Response(
            content=data,
            media_type=meta.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{key.split("/")[-1]}"',
                "ETag": meta.etag,
            },
        )
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail=f"Object not found: {key}")
    except StoragePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.delete("/{key:path}")
async def delete_object(
    key: str,
    storage=Depends(_get_storage),
):
    """Delete an object from storage."""
    try:
        deleted = await storage.delete(key)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Object not found: {key}")
        return {"status": "deleted", "key": key}
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail=f"Object not found: {key}")
    except StoragePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
