import httpx

from src.core.configuration import settings


class StorageClient:
    async def store_requirement_source(
        self,
        project_id: str,
        document_id: str,
        filename: str,
        content_type: str | None,
        data: bytes,
    ) -> dict:
        async with httpx.AsyncClient(
            timeout=settings.INTERNAL_LONG_REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = await client.post(
                f"{settings.CLOUD_URL.rstrip('/')}/noi-bo/kiem-thu/nguon-yeu-cau",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                data={"project_id": project_id, "document_id": document_id},
                files={
                    "file": (
                        filename,
                        data,
                        content_type or "application/octet-stream",
                    )
                },
            )
        response.raise_for_status()
        return response.json()["data"]

    async def read_requirement_source(
        self,
        project_id: str,
        document_id: str,
        object_key: str,
    ) -> bytes:
        async with httpx.AsyncClient(
            timeout=settings.INTERNAL_LONG_REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = await client.get(
                f"{settings.CLOUD_URL.rstrip('/')}/noi-bo/kiem-thu/nguon-yeu-cau",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                params={
                    "project_id": project_id,
                    "document_id": document_id,
                    "object_key": object_key,
                },
            )
        response.raise_for_status()
        return response.content


storage_client = StorageClient()
