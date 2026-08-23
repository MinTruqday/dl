import aioboto3
from botocore.exceptions import ClientError

from src.core.infrastructure.configuration import settings


session = aioboto3.Session()
storage_client = None


async def get_storage_client():
    global storage_client
    if storage_client is None:
        storage_client = await session.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
        ).__aenter__()
    return storage_client


async def init_storage():
    client = await get_storage_client()
    try:
        await client.head_bucket(Bucket=settings.MINIO_PRIVATE_BUCKET)
    except ClientError as error:
        code = str(error.response.get("Error", {}).get("Code", ""))
        if code not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        await client.create_bucket(Bucket=settings.MINIO_PRIVATE_BUCKET)


async def upload_pdf(path: str, content: bytes):
    client = await get_storage_client()
    await client.put_object(
        Bucket=settings.MINIO_PRIVATE_BUCKET, Key=path, Body=content, ContentType="application/pdf"
    )


async def storage_ready() -> bool:
    client = await get_storage_client()
    await client.head_bucket(Bucket=settings.MINIO_PRIVATE_BUCKET)
    return True


async def close_storage():
    global storage_client
    if storage_client is not None:
        await storage_client.__aexit__(None, None, None)
        storage_client = None
