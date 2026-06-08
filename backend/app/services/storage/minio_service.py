"""File storage service using boto3 (S3-compatible — works with Supabase Storage)."""
import boto3
from botocore.client import Config
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def get_storage_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.MINIO_ENDPOINT}/storage/v1/s3",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="ap-south-1",
        )
        # Ensure buckets exist
        existing = [b["Name"] for b in _client.list_buckets().get("Buckets", [])]
        for bucket in [settings.MINIO_BUCKET_DOCUMENTS, settings.MINIO_BUCKET_REPORTS]:
            if bucket not in existing:
                _client.create_bucket(Bucket=bucket)
                logger.info(f"Created bucket: {bucket}")
    return _client


async def upload_file(
    bucket: str,
    path: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    client = get_storage_client()
    client.put_object(
        Bucket=bucket,
        Key=path,
        Body=data,
        ContentType=content_type,
    )
    return path


async def download_file(bucket: str, path: str) -> bytes:
    client = get_storage_client()
    response = client.get_object(Bucket=bucket, Key=path)
    return response["Body"].read()


async def delete_file(bucket: str, path: str):
    client = get_storage_client()
    client.delete_object(Bucket=bucket, Key=path)


def get_file_url(bucket: str, path: str, expires_seconds: int = 3600) -> str:
    client = get_storage_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": path},
        ExpiresIn=expires_seconds,
    )