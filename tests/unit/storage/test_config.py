# -*- coding: utf-8 -*-
"""
Tests for StorageConfig configuration model.

Covers T-STORAGE-001.7 (factory switching via config).
"""
import os
from unittest.mock import patch

import pytest

from copaw.storage.config import StorageConfig


class TestStorageConfigDefaults:
    """Default values for StorageConfig."""

    def test_default_backend_is_filesystem(self):
        cfg = StorageConfig()
        assert cfg.backend == "filesystem"

    def test_default_bucket(self):
        cfg = StorageConfig()
        assert cfg.default_bucket == "copaw-data"

    def test_default_presign(self):
        cfg = StorageConfig()
        assert cfg.presign_enabled is True
        assert cfg.presign_expire_seconds == 3600

    def test_default_metadata_sync(self):
        cfg = StorageConfig()
        assert cfg.metadata_sync_enabled is True

    def test_default_filesystem_base_dir(self):
        cfg = StorageConfig()
        assert cfg.filesystem_base_dir == "~/.copaw"

    def test_default_minio_settings(self):
        cfg = StorageConfig()
        assert cfg.minio_endpoint == "localhost:9000"
        assert cfg.minio_secure is False

    def test_default_sftp_settings(self):
        cfg = StorageConfig()
        assert cfg.sftp_host == "localhost"
        assert cfg.sftp_port == 22


class TestStorageConfigBackendSwitching:
    """T-STORAGE-001.7: Dynamic backend switching via configuration."""

    def test_s3_backend(self):
        cfg = StorageConfig(backend="s3")
        assert cfg.backend == "s3"

    def test_minio_backend(self):
        cfg = StorageConfig(backend="minio")
        assert cfg.backend == "minio"

    def test_oss_backend(self):
        cfg = StorageConfig(backend="oss")
        assert cfg.backend == "oss"

    def test_sftp_backend(self):
        cfg = StorageConfig(backend="sftp")
        assert cfg.backend == "sftp"

    def test_invalid_backend_rejected(self):
        with pytest.raises(Exception):
            StorageConfig(backend="invalid")

    def test_effective_bucket_s3(self):
        cfg = StorageConfig(backend="s3", s3_bucket="my-bucket")
        assert cfg.effective_bucket() == "my-bucket"

    def test_effective_bucket_minio(self):
        cfg = StorageConfig(backend="minio", minio_bucket="minio-data")
        assert cfg.effective_bucket() == "minio-data"

    def test_effective_bucket_oss(self):
        cfg = StorageConfig(backend="oss", oss_bucket_name="oss-data")
        assert cfg.effective_bucket() == "oss-data"

    def test_effective_bucket_fallback(self):
        cfg = StorageConfig(backend="filesystem")
        assert cfg.effective_bucket() == cfg.default_bucket


class TestStorageConfigFromEnv:
    """Configuration from COPAW_STORAGE_* environment variables."""

    def test_from_env_defaults(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove any COPAW_STORAGE_ vars
            env_copy = {k: v for k, v in os.environ.items() if not k.startswith("COPAW_STORAGE_")}
            with patch.dict(os.environ, env_copy, clear=True):
                cfg = StorageConfig.from_env()
                assert cfg.backend == "filesystem"

    def test_from_env_backend(self):
        with patch.dict(os.environ, {"COPAW_STORAGE_BACKEND": "s3"}):
            cfg = StorageConfig.from_env()
            assert cfg.backend == "s3"

    def test_from_env_s3_settings(self):
        with patch.dict(os.environ, {
            "COPAW_STORAGE_BACKEND": "s3",
            "COPAW_S3_ENDPOINT_URL": "https://s3.example.com",
            "COPAW_S3_ACCESS_KEY": "AKIA123",
            "COPAW_S3_SECRET_KEY": "secret123",
            "COPAW_S3_REGION": "ap-southeast-1",
        }):
            cfg = StorageConfig.from_env()
            assert cfg.s3_endpoint_url == "https://s3.example.com"
            assert cfg.s3_access_key == "AKIA123"
            assert cfg.s3_region == "ap-southeast-1"

    def test_from_env_minio_settings(self):
        with patch.dict(os.environ, {
            "COPAW_STORAGE_BACKEND": "minio",
            "COPAW_MINIO_ENDPOINT": "minio.corp:9000",
            "COPAW_MINIO_ACCESS_KEY": "minioadmin",
        }):
            cfg = StorageConfig.from_env()
            assert cfg.minio_endpoint == "minio.corp:9000"

    def test_from_env_filesystem_dir(self):
        with patch.dict(os.environ, {
            "COPAW_FILESYSTEM_BASE_DIR": "/tmp/copaw-test",
        }):
            cfg = StorageConfig.from_env()
            assert cfg.filesystem_base_dir == "/tmp/copaw-test"
