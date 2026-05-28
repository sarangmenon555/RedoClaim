"""MinIO object storage service (S3-compatible, self-hosted, free)."""
import io
import logging
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        # Ensure buckets exist
        for bucket in [settings.MINIO_BUCKET_DOCUMENTS, settings.MINIO_BUCKET_REPORTS]:
            if not _client.bucket_exists(bucket):
                _client.make_bucket(bucket)
                logger.info(f"Created MinIO bucket: {bucket}")
    return _client


async def upload_file(
    bucket: str,
    path: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload file to MinIO. Returns the object path."""
    client = get_minio_client()
    client.put_object(
        bucket_name=bucket,
        object_name=path,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return path


async def download_file(bucket: str, path: str) -> bytes:
    """Download file from MinIO."""
    client = get_minio_client()
    response = client.get_object(bucket, path)
    return response.read()


async def delete_file(bucket: str, path: str):
    """Delete file from MinIO (for GDPR right-to-erasure)."""
    client = get_minio_client()
    client.remove_object(bucket, path)


def get_file_url(bucket: str, path: str, expires_seconds: int = 3600) -> str:
    """Generate a presigned URL for temporary file access."""
    from datetime import timedelta
    client = get_minio_client()
    return client.presigned_get_object(
        bucket, path, expires=timedelta(seconds=expires_seconds)
    )
