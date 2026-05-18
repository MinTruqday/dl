from minio import Minio
import os
from loguru import logger
import asyncio

class CollectorStorage:
    def __init__(self):
        endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
        if endpoint.startswith("http://"):
            endpoint = endpoint[7:]
        elif endpoint.startswith("https://"):
            endpoint = endpoint[8:]
        
        self.client = Minio(
            endpoint,
            access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.environ.get("MINIO_SECRET_KEY", "miniopassword"),
            secure=False
        )
        self.bucket = os.environ.get("MINIO_BUCKET_NAME", "doclib-books")
        self.public_url = os.environ.get("MINIO_PUBLIC_URL", "http://localhost:9000")
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            logger.error(f"Failed to ensure MinIO bucket exists: {e}")
            raise e

    async def upload_local_file(self, object_name: str, local_file_path: str, content_type: str = "application/pdf") -> str:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.fput_object(
                    bucket_name=self.bucket,
                    object_name=object_name,
                    file_path=local_file_path,
                    content_type=content_type
                )
            )
            url = f"{self.public_url}/{self.bucket}/{object_name}"
            return url
        except Exception as e:
            logger.error(f"Failed to upload local file {local_file_path} to MinIO: {e}")
            raise e

storage = CollectorStorage()
