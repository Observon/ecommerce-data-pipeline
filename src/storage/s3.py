"""AWS S3 publication for immutable RAW and processed pipeline artifacts."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)


class StorageError(RuntimeError):
    """Raised when an artifact cannot be published to object storage."""


@dataclass(frozen=True)
class S3Settings:
    bucket: str
    region: str
    raw_prefix: str = "raw"
    processed_prefix: str = "processed"

    @classmethod
    def from_environment(cls) -> "S3Settings":
        load_dotenv()
        bucket = os.getenv("S3_BUCKET", "").strip()
        if not bucket:
            raise StorageError("S3_BUCKET must be set when --upload-s3 is used.")
        return cls(
            bucket=bucket,
            region=os.getenv("AWS_REGION", "us-east-1"),
            raw_prefix=os.getenv("S3_RAW_PREFIX", "raw").strip("/"),
            processed_prefix=os.getenv("S3_PROCESSED_PREFIX", "processed").strip("/"),
        )


class S3Publisher:
    """Publish local files to S3 while preserving their layer and relative path."""

    def __init__(self, settings: S3Settings, client: Any | None = None) -> None:
        self.settings = settings
        self.client = client or boto3.client("s3", region_name=settings.region)

    def upload_raw_directory(self, raw_directory: Path) -> list[str]:
        """Upload original source CSVs without changing their names or content."""
        return self._upload_directory(raw_directory, self.settings.raw_prefix, {".csv"}, include_directory_name=True)

    def upload_processed_directory(self, processed_directory: Path) -> list[str]:
        """Upload processed Parquet, quality report, and quarantine artifacts."""
        return self._upload_directory(processed_directory, self.settings.processed_prefix, {".parquet", ".json"})

    def _upload_directory(
        self,
        directory: Path,
        prefix: str,
        extensions: set[str],
        include_directory_name: bool = False,
    ) -> list[str]:
        if not directory.is_dir():
            raise StorageError(f"Directory does not exist: {directory}")

        keys: list[str] = []
        for file_path in sorted(directory.rglob("*")):
            if not file_path.is_file() or file_path.suffix.lower() not in extensions:
                continue
            relative_path = file_path.relative_to(directory).as_posix()
            key_parts = [prefix]
            if include_directory_name:
                key_parts.append(directory.name)
            key_parts.append(relative_path)
            key = "/".join(key_parts)
            try:
                self.client.upload_file(str(file_path), self.settings.bucket, key)
            except (BotoCoreError, ClientError, OSError) as error:
                raise StorageError(f"Failed to upload {file_path} to s3://{self.settings.bucket}/{key}") from error
            LOGGER.info("Uploaded s3://%s/%s", self.settings.bucket, key)
            keys.append(key)
        return keys
