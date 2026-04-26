import os
import io
import tempfile
from pathlib import Path
from loguru import logger
from typing import Dict, Optional, List

import boto3

class ADEAgent:
    def __init__(self):
        self._minio_base = os.environ.get("MINIO_ENDPOINT").rstrip("/")
        self._bucket = os.environ.get("MINIO_BUCKET_NAME")
        self._minio_access = os.environ.get("MINIO_ACCESS_KEY")
        self._minio_secret = os.environ.get("MINIO_SECRET_KEY")
        self._minio_region = os.environ.get("MINIO_REGION")
        self._ade_model = os.environ.get("ADE_MODEL")

        logger.info("ADE Agent initialized with LandingAI ADE")

    async def _get_client(self):
        from landingai_ade import AsyncLandingAIADE, DefaultAioHttpClient
        return AsyncLandingAIADE(
            apikey=os.environ["VISION_AGENT_API_KEY"],
            http_client=DefaultAioHttpClient(),
        )

    async def parse_document(self, file_url: str) -> Dict:
        file_bytes, file_ext = await self._download_from_minio(file_url)
        if not file_bytes:
            return {"error": f"Cannot download file: {file_url}"}

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            client = await self._get_client()
            async with client as current_client:
                response = await current_client.parse(
                    document=tmp_path,
                    model=self._ade_model,
                    split="page"
                )

            markdown = response.markdown if response.markdown else ""
            chunks = []
            
            if response.chunks:
                for item in response.chunks:
                    text = item.text.strip() if item.text else ""
                    if len(text) > 10:
                        chunks.append({
                            "text": text,
                            "chunk_type": item.type if hasattr(item, "type") else "text",
                        })

            if not chunks and markdown:
                sections = markdown.split("\n\n")
                for section in sections:
                    if len(section.strip()) > 30:
                        chunks.append({
                            "text": section.strip(),
                            "chunk_type": "text",
                        })

            output = {
                "markdown": markdown,
                "chunks": chunks,
                "chunk_count": len(chunks),
            }

            logger.info(f"LandingAI ADE parsed: {len(chunks)} chunks, {len(markdown)} chars markdown")
            return output

        except Exception as e:
            logger.error(f"LandingAI ADE parse error: {e}")
            return {"error": str(e)}
        finally:
            tmp_path.unlink(missing_ok=True)

    async def get_ade_chunks_for_ingestion(self, file_url: str) -> List[Dict]:
        parse_result = await self.parse_document(file_url)
        if parse_result.get("error"):
            logger.warning(f"LandingAI ADE failed: {parse_result['error']}")
            return []

        chunks = parse_result.get("chunks", [])

        ingestion_chunks = []
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            if len(text.strip()) < 30:
                continue
            ingestion_chunks.append({
                "text": text,
                "chunk_type": chunk.get("chunk_type", "text"),
                "index": i,
            })

        logger.info(f"LandingAI ADE produced {len(ingestion_chunks)} chunks for ingestion")
        return ingestion_chunks

    async def get_markdown(self, file_url: str) -> str:
        parse_result = await self.parse_document(file_url)
        return parse_result.get("markdown", "")

    async def _download_from_minio(self, file_url: str) -> tuple:
        try:
            from urllib.parse import urlparse

            if file_url.startswith("http"):
                parsed = urlparse(file_url)
                path_parts = parsed.path.lstrip("/").split("/", 1)
                bucket = path_parts[0] if len(path_parts) == 2 else self._bucket
                object_key = path_parts[1] if len(path_parts) == 2 else parsed.path.lstrip("/")
            else:
                bucket = self._bucket
                object_key = file_url

            s3 = boto3.client(
                "s3",
                endpoint_url=self._minio_base,
                aws_access_key_id=self._minio_access,
                aws_secret_access_key=self._minio_secret,
                region_name=self._minio_region,
            )
            obj = s3.get_object(Bucket=bucket, Key=object_key)
            data = obj["Body"].read()

            ext = ".pdf"
            if object_key.endswith(".epub"):
                ext = ".epub"
            elif object_key.endswith(".docx"):
                ext = ".docx"

            logger.info(f"Downloaded {len(data)} bytes from MinIO for ADE")
            return data, ext

        except Exception as e:
            logger.error(f"MinIO download failed: {e}")
            return None, ""

ade_agent = ADEAgent()

