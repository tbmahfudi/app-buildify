"""S3-compatible blob storage (MinIO in dev, S3/Azure/MinIO in prod).

Blobs are addressed by `{tenant_id}/{document_id}/{version}` so a tenant's
objects share a key prefix — isolation is enforced in code (every call is made
under a resolved tenant) and mirrored by the DB RLS on the metadata rows.

boto3 is synchronous; calls are dispatched to a threadpool so they never block
the event loop.
"""

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi.concurrency import run_in_threadpool

from ..config import settings


def _client(endpoint_url: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.STORAGE_SECRET_KEY,
        region_name=settings.STORAGE_REGION,
        config=Config(signature_version="s3v4"),
    )


class StorageService:
    """Thin async wrapper over an S3 bucket."""

    def __init__(self) -> None:
        self._s3 = _client(settings.STORAGE_ENDPOINT_URL)
        # Separate client bound to the browser-reachable endpoint, used only for
        # signing URLs handed back to clients.
        self._s3_public = _client(settings.STORAGE_PUBLIC_ENDPOINT_URL)
        self._bucket = settings.STORAGE_BUCKET

    def _ensure_bucket_sync(self) -> None:
        try:
            self._s3.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._s3.create_bucket(Bucket=self._bucket)

    async def ensure_bucket(self) -> None:
        await run_in_threadpool(self._ensure_bucket_sync)

    @staticmethod
    def object_key(tenant_id: str, document_id: str, version: int) -> str:
        return f"{tenant_id}/{document_id}/{version}"

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await run_in_threadpool(
            lambda: self._s3.put_object(
                Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
            )
        )

    async def delete(self, key: str) -> None:
        await run_in_threadpool(
            lambda: self._s3.delete_object(Bucket=self._bucket, Key=key)
        )

    def _get_bytes_sync(self, key: str) -> bytes:
        resp = self._s3.get_object(Bucket=self._bucket, Key=key)
        return resp["Body"].read()

    async def get_bytes(self, key: str) -> bytes:
        """Fetch a blob's bytes server-side (used to assemble zip archives)."""
        return await run_in_threadpool(self._get_bytes_sync, key)

    async def presigned_get_url(
        self, key: str, filename: str, content_type: str
    ) -> str:
        params = {
            "Bucket": self._bucket,
            "Key": key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
            "ResponseContentType": content_type,
        }
        return await run_in_threadpool(
            lambda: self._s3_public.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=settings.PRESIGN_EXPIRY_SECONDS,
            )
        )


storage = StorageService()
