import asyncio
import logging
import re

import boto3
from botocore.client import Config

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def _normalize_host(raw: str) -> str:
    host = (raw or "").strip()
    host = re.sub(r"^https?://", "", host)
    host = host.split("/")[0]
    return host


def get_storage_client():
    global _client
    if _client is None:
        host = _normalize_host(settings.MINIO_ENDPOINT)
        endpoint = f"https://{host}/storage/v1/s3"
        logger.info(f"Storage endpoint: {endpoint}")
        _client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                connect_timeout=5,
                read_timeout=20,
                retries={"max_attempts": 2, "mode": "standard"},
            ),
            region_name="ap-south-1",
        )
        try:
            existing = [b["Name"] for b in _client.list_buckets().get("Buckets", [])]
            for bucket in [settings.MINIO_BUCKET_DOCUMENTS, settings.MINIO_BUCKET_REPORTS]:
                if bucket not in existing:
                    _client.create_bucket(Bucket=bucket)
                    logger.info(f"Created bucket: {bucket}")
        except Exception as e:
            logger.warning(f"Bucket check skipped ({type(e).__name__}): {e!r}")
    return _client


async def upload_file(
    bucket: str,
    path: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    client = get_storage_client()
    try:
        await asyncio.to_thread(
            client.put_object,
            Bucket=bucket,
            Key=path,
            Body=data,
            ContentType=content_type,
        )
    except Exception as e:
        logger.error(f"Storage put_object failed ({type(e).__name__}): {e!r}")
        raise
    return path


async def download_file(bucket: str, path: str) -> bytes:
    client = get_storage_client()

    def _get() -> bytes:
        return client.get_object(Bucket=bucket, Key=path)["Body"].read()

    return await asyncio.to_thread(_get)


async def delete_file(bucket: str, path: str):
    client = get_storage_client()
    await asyncio.to_thread(client.delete_object, Bucket=bucket, Key=path)


def get_file_url(bucket: str, path: str, expires_seconds: int = 3600) -> str:
    client = get_storage_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": path},
        ExpiresIn=expires_seconds,
    )