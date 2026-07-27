import aioboto3
import brotli
from botocore.exceptions import ClientError
from loguru import logger

from src.core.infrastructure.configuration import settings

MINIO_ENDPOINT = settings.MINIO_ENDPOINT
MINIO_ACCESS_KEY = settings.MINIO_ACCESS_KEY
MINIO_SECRET_KEY = settings.MINIO_SECRET_KEY
MINIO_PRIVATE_BUCKET = settings.MINIO_PRIVATE_BUCKET
MINIO_PUBLIC_BUCKET = settings.MINIO_PUBLIC_BUCKET
MINIO_PUBLIC_URL = settings.MINIO_PUBLIC_URL

def get_bucket(path: str) -> str:
    if path.startswith("system/"):
        return MINIO_PRIVATE_BUCKET
    return MINIO_PUBLIC_BUCKET

session = aioboto3.Session()
_storage_client = None

async def get_storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = await session.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
        ).__aenter__()
    return _storage_client

async def close_storage_client():
    global _storage_client
    if _storage_client is not None:
        await _storage_client.__aexit__(None, None, None)
        _storage_client = None

async def initialize_bucket():
    storage_client = await get_storage_client()
    for bucket in [MINIO_PRIVATE_BUCKET, MINIO_PUBLIC_BUCKET]:
        try:
            await storage_client.head_bucket(Bucket=bucket)
        except ClientError as e:
            logger.info(f"Initializing storage bucket {bucket}")
            await storage_client.create_bucket(Bucket=bucket)
            logger.info(f"Storage bucket initialized {bucket}")

async def upload_file(
    file_content: bytes,
    object_name: str,
    content_type: str = "application/pdf",
    compress: bool = False,
) -> str:
    kwargs = {
        "Bucket": get_bucket(object_name),
        "Key": object_name,
        "ContentType": content_type,
    }

    if (
        compress
        or content_type.startswith("text/")
        or content_type == "application/json"
    ):
        import asyncio

        loop = asyncio.get_event_loop()
        file_content = await loop.run_in_executor(
            None, lambda: brotli.compress(file_content, quality=11)
        )
        kwargs["ContentEncoding"] = "br"

    kwargs["Body"] = file_content

    storage_client = await get_storage_client()
    await storage_client.put_object(**kwargs)
    return object_name

async def download_file(object_name: str) -> tuple[bytes, str]:
    storage_client = await get_storage_client()
    response = await storage_client.get_object(
        Bucket=get_bucket(object_name), Key=object_name
    )
    content = await response["Body"].read()

    if response.get("ContentEncoding") == "br":
        content = brotli.decompress(content)

    return content, response.get("ContentType", "application/octet-stream")

async def generate_presigned_url(object_name: str, expiration: int = 3600) -> str:
    storage_client = await get_storage_client()
    params = {"Bucket": get_bucket(object_name), "Key": object_name}

    response = await storage_client.generate_presigned_url(
        "get_object", Params=params, ExpiresIn=expiration
    )
    if MINIO_PUBLIC_URL and MINIO_ENDPOINT in response:
        response = response.replace(MINIO_ENDPOINT, MINIO_PUBLIC_URL)
    return response
