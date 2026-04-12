# -*- coding: utf-8 -*-
"""
Unified storage configuration model.

Embedded into EnterpriseConfig so that storage backend can be
switched purely through configuration / environment variables.
"""
from __future__ import annotations

import os
from typing import Literal, Optional

from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """Unified storage configuration — embedded into EnterpriseConfig."""

    backend: Literal["filesystem", "s3", "minio", "oss", "sftp"] = Field(
        default="filesystem",
        description="Storage backend type. Personal edition defaults to filesystem; "
        "enterprise edition should use s3/minio.",
    )

    # -- Common settings --------------------------------------------------- #

    default_bucket: str = Field(
        default="copaw-data",
        description="Default bucket / namespace",
    )
    presign_enabled: bool = Field(
        default=True,
        description="Enable pre-signed URL generation for large file direct upload",
    )
    presign_expire_seconds: int = Field(
        default=3600,
        description="Pre-signed URL expiration time in seconds",
    )

    # -- Metadata sync ---------------------------------------------------- #

    metadata_sync_enabled: bool = Field(
        default=True,
        description="Sync object metadata to PostgreSQL after upload",
    )

    # -- S3 compatible settings ------------------------------------------- #

    s3_endpoint_url: str = Field(
        default="",
        description="S3 endpoint URL (empty = AWS native)",
    )
    s3_access_key: str = Field(default="", description="S3 Access Key")
    s3_secret_key: str = Field(default="", description="S3 Secret Key")
    s3_region: str = Field(default="us-east-1", description="S3 region")
    s3_bucket: str = Field(
        default="copaw-data",
        description="S3 bucket name (overrides default_bucket for S3)",
    )

    # -- MinIO settings --------------------------------------------------- #

    minio_endpoint: str = Field(
        default="localhost:9000",
        description="MinIO endpoint (host:port)",
    )
    minio_access_key: str = Field(default="", description="MinIO Access Key")
    minio_secret_key: str = Field(default="", description="MinIO Secret Key")
    minio_secure: bool = Field(
        default=False,
        description="Use HTTPS for MinIO connection",
    )
    minio_bucket: str = Field(
        default="copaw-data",
        description="MinIO bucket name",
    )

    # -- Alibaba Cloud OSS settings --------------------------------------- #

    oss_endpoint: str = Field(default="", description="OSS endpoint URL")
    oss_access_key_id: str = Field(default="", description="OSS AccessKey ID")
    oss_access_key_secret: str = Field(
        default="", description="OSS AccessKey Secret"
    )
    oss_bucket_name: str = Field(
        default="copaw-data",
        description="OSS bucket name",
    )

    # -- SFTP settings ---------------------------------------------------- #

    sftp_host: str = Field(default="localhost", description="SFTP server host")
    sftp_port: int = Field(default=22, description="SFTP server port")
    sftp_username: str = Field(default="", description="SFTP username")
    sftp_password: str = Field(default="", description="SFTP password")
    sftp_private_key_path: str = Field(
        default="", description="Path to SSH private key for SFTP auth"
    )
    sftp_base_dir: str = Field(
        default="/data/copaw",
        description="Base directory on the SFTP server",
    )

    # -- FileSystem settings (personal edition) --------------------------- #

    filesystem_base_dir: str = Field(
        default="~/.copaw",
        description="Local filesystem root directory for personal edition",
    )

    # -- Helpers ---------------------------------------------------------- #

    def effective_bucket(self) -> str:
        """Return the bucket name for the currently selected backend."""
        if self.backend == "s3":
            return self.s3_bucket or self.default_bucket
        if self.backend == "minio":
            return self.minio_bucket or self.default_bucket
        if self.backend == "oss":
            return self.oss_bucket_name or self.default_bucket
        return self.default_bucket

    @classmethod
    def from_env(cls) -> "StorageConfig":
        """Create a StorageConfig from COPAW_STORAGE_* environment variables."""
        return cls(
            backend=os.environ.get("COPAW_STORAGE_BACKEND", "filesystem"),  # type: ignore[arg-type]
            default_bucket=os.environ.get("COPAW_STORAGE_BUCKET", "copaw-data"),
            s3_endpoint_url=os.environ.get("COPAW_S3_ENDPOINT_URL", ""),
            s3_access_key=os.environ.get("COPAW_S3_ACCESS_KEY", ""),
            s3_secret_key=os.environ.get("COPAW_S3_SECRET_KEY", ""),
            s3_region=os.environ.get("COPAW_S3_REGION", "us-east-1"),
            minio_endpoint=os.environ.get("COPAW_MINIO_ENDPOINT", "localhost:9000"),
            minio_access_key=os.environ.get("COPAW_MINIO_ACCESS_KEY", ""),
            minio_secret_key=os.environ.get("COPAW_MINIO_SECRET_KEY", ""),
            filesystem_base_dir=os.environ.get(
                "COPAW_FILESYSTEM_BASE_DIR", "~/.copaw"
            ),
        )
