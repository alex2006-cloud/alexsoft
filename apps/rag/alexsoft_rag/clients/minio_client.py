"""MinIO (S3) access for source documents. The SDK is synchronous -> run in threads."""

from __future__ import annotations

import asyncio

from minio import Minio
from minio.error import S3Error

from ..errors import ApiError, upstream


class ObjectStore:
    def __init__(
        self, endpoint: str, access_key: str, secret_key: str, bucket: str, *, secure: bool = False
    ) -> None:
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self.default_bucket = bucket

    async def ensure_bucket(self) -> None:
        def _do() -> None:
            if not self._client.bucket_exists(self.default_bucket):
                self._client.make_bucket(self.default_bucket)

        await asyncio.to_thread(_do)

    async def is_alive(self) -> bool:
        try:
            await asyncio.to_thread(self._client.bucket_exists, self.default_bucket)
            return True
        except Exception:
            return False

    async def get_object(
        self, bucket: str, key: str, version_id: str | None = None, *, max_bytes: int
    ) -> bytes:
        def _do() -> bytes:
            resp = self._client.get_object(bucket, key, version_id=version_id)
            try:
                data = resp.read(max_bytes + 1)
            finally:
                resp.close()
                resp.release_conn()
            return data

        try:
            data = await asyncio.to_thread(_do)
        except S3Error as e:
            if e.code in {"NoSuchKey", "NoSuchBucket", "NoSuchVersion"}:
                raise ApiError(
                    404, "not_found", f"Object s3://{bucket}/{key} not found ({e.code})"
                ) from e
            raise upstream("object_store_unavailable", f"MinIO error: {e.code}") from e
        except Exception as e:  # network errors, etc.
            raise upstream("object_store_unavailable", f"MinIO request failed: {e}") from e
        if len(data) > max_bytes:
            raise ApiError(413, "payload_too_large", f"Object exceeds {max_bytes} bytes")
        return data
