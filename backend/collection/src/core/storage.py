import os

import aioboto3
from botocore.exceptions import ClientError
from loguru import logger

from src.core.infrastructure.configuration import settings

class StorageService:
    def __init__(self):
        endpoint = settings.MINIO_ENDPOINT
        if not endpoint.startswith("http"):
            endpoint = f"http://{endpoint}"

        self.endpoint = endpoint
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY

        if not self.access_key or not self.secret_key:
            raise ValueError("Missing MinIO authentication keys (MINIO_ACCESS_KEY or MINIO_SECRET_KEY)")

        self.private_bucket = settings.MINIO_PRIVATE_BUCKET
        self.public_bucket = settings.MINIO_PUBLIC_BUCKET
        self.public_url = settings.MINIO_PUBLIC_URL

        self.session = aioboto3.Session()
        self._storage_client = None

    async def get_client(self):
        if self._storage_client is None:
            self._storage_client = await self.session.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ).__aenter__()
        return self._storage_client

    def get_bucket(self, path: str) -> str:
        if path.startswith(("system/", "users/", "client/", "temp/")):
            return self.private_bucket
        return self.public_bucket

    async def _ensure_bucket(self):
        try:
            client = await self.get_client()
            for bucket in [self.private_bucket, self.public_bucket]:
                try:
                    await client.head_bucket(Bucket=bucket)
                except ClientError:
                    logger.exception(f"Initializing MinIO bucket {bucket}")
                    await client.create_bucket(Bucket=bucket)
        except Exception:
            logger.exception("MinIO bucket initialization failed")
            raise

    async def upload_local_file(
        self,
        object_name: str,
        local_file_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        try:
            await self._ensure_bucket()
            client = await self.get_client()
            target_bucket = self.get_bucket(object_name)
            await client.upload_file(
                Filename=local_file_path,
                Bucket=target_bucket,
                Key=object_name,
                ExtraArgs={"ContentType": content_type},
            )
            return object_name
        except Exception:
            logger.exception("Network error during permanent file storage upload")
            raise

    async def health_check(self):
        client = await self.get_client()
        await client.head_bucket(Bucket=self.private_bucket)
        await client.head_bucket(Bucket=self.public_bucket)
        return True

    async def aclose(self):
        if self._storage_client is not None:
            await self._storage_client.__aexit__(None, None, None)
            self._storage_client = None

storage = StorageService()
