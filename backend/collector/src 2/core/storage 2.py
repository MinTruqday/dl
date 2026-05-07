import os
import aiohttp
from minio import Minio
from loguru import logger
import io

class MinioStorage:
    def __init__(self):
        self.endpoint = os.environ.get("MINIO_ENDPOINT").replace("http://", "").replace("https://", "")
        self.access = os.environ.get("MINIO_ACCESS_KEY")
        self.secret = os.environ.get("MINIO_SECRET_KEY")
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access,
            secret_key=self.secret,
            secure=False
        )
        self.bucket = os.environ.get("MINIO_BUCKET_NAME")
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            policy = (
                '{"Version":"2012-10-17","Statement":[{"Action":["s3:GetObject"],"Effect":"Allow","Principal":{"AWS":["*"]},"Resource":["arn:aws:s3:::'
                + self.bucket
                + '/*"]}]}'
            )
            self.client.set_bucket_policy(self.bucket, policy)

    async def upload_from_url(self, file_name: str, url: str, cookies: dict = None) -> str:
        
        try:
            async with aiohttp.ClientSession(cookies=cookies) as session:
                headers = {'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                async with session.get(url, headers=headers, timeout=300) as resp:
                    if resp.status != 200:
                        raise Exception(f"S3 Download Error/Download Block {resp.status} from {url}")
                    
                    data = await resp.read()
                    data_len = len(data)
                    
                    self.client.put_object(
                        self.bucket,
                        file_name,
                        io.BytesIO(data),
                        data_len,
                        content_type="application/epub+zip" if file_name.endswith('.epub') else "application/pdf"
                    )
logger.info("Log message sanitized"))
                    return f"http://{self.endpoint}/{self.bucket}/{file_name}"
        except Exception as e:
logger.info("Log message sanitized"))
            return None

    async def upload_local_file(self, object_name: str, file_path: str) -> str:
        
        try:
            with open(file_path, 'rb') as f:
                size = os.path.getsize(file_path)
                self.client.put_object(
                    self.bucket,
                    object_name,
                    f,
                    size,
                    content_type="application/pdf"
                )
logger.info("Log message sanitized"))
                return f"http://{self.endpoint}/{self.bucket}/{object_name}"
        except Exception as e:
logger.info("Log message sanitized"))
            return ""

storage = MinioStorage()
