import os

import aioboto3
from botocore.exceptions import ClientError
from loguru import logger

from core.infrastructure.app_config import settings


class DataCollectionStorage:
    def __init__(self):
        endpoint = settings.MINIO_ENDPOINT or "minio:9000"
        if not endpoint.startswith("http"):
            endpoint = f"http://{endpoint}"

        self.endpoint = endpoint
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY

        if not self.access_key or not self.secret_key:
            raise ValueError("Thiếu thông tin khóa bảo mật")

        self.bucket = settings.MINIO_BUCKET_NAME
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

    async def _ensure_bucket(self):
        try:
            client = await self.get_client()
            await client.head_bucket(Bucket=self.bucket)
        except ClientError:
            logger.info("Đang khởi tạo không gian lưu trữ đa phương tiện")
            client = await self.get_client()
            await client.create_bucket(Bucket=self.bucket)

    async def upload_local_file(
        self,
        object_name: str,
        local_file_path: str,
        content_type: str = "application/pdf",
    ) -> str:
        try:
            await self._ensure_bucket()
            client = await self.get_client()
            await client.upload_file(
                Filename=local_file_path,
                Bucket=self.bucket,
                Key=object_name,
                ExtraArgs={"ContentType": content_type},
            )
            url = f"{self.public_url}/{self.bucket}/{object_name}"
            return url
        except Exception as e:
            logger.error("Lỗi mạng khi lưu tệp vĩnh viễn")
            raise e


storage = DataCollectionStorage()
