from loguru import logger
import os
import aioboto3
from botocore.exceptions import ClientError

from core.config import settings

MINIO_ENDPOINT = settings.MINIO_ENDPOINT
MINIO_ACCESS_KEY = settings.MINIO_ACCESS_KEY
MINIO_SECRET_KEY = settings.MINIO_SECRET_KEY
MINIO_BUCKET_NAME = settings.MINIO_BUCKET_NAME
MINIO_PUBLIC_URL = settings.MINIO_PUBLIC_URL

session = aioboto3.Session()

async def get_s3_client():
    return session.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
    )

async def initialize_bucket():
    async with await get_s3_client() as s3:
        try:
            await s3.head_bucket(Bucket=MINIO_BUCKET_NAME)
        except ClientError:
            logger.info(f"Bucket {MINIO_BUCKET_NAME} not found. Creating")
            await s3.create_bucket(Bucket=MINIO_BUCKET_NAME)
            logger.info(f"Bucket {MINIO_BUCKET_NAME} created successfully.")

async def upload_file(file_content: bytes, object_name: str, content_type: str = "application/pdf") -> str:
    async with await get_s3_client() as s3:
        await s3.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=object_name,
            Body=file_content,
            ContentType=content_type
        )
    return object_name

async def generate_presigned_url(object_name: str, expiration: int = 3600) -> str:
    async with await get_s3_client() as s3:
        response = await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": MINIO_BUCKET_NAME, "Key": object_name},
            ExpiresIn=expiration
        )
        if MINIO_PUBLIC_URL and MINIO_ENDPOINT in response:
            response = response.replace(MINIO_ENDPOINT, MINIO_PUBLIC_URL)
        return response
