import httpx

from src.core.configuration import settings


class WorkerClientError(RuntimeError):
    def __init__(self, status_code: int | None = None):
        super().__init__("worker_request_failed")
        self.status_code = status_code


class WorkerClient:
    @staticmethod
    async def request(method: str, path: str, payload: dict | None = None):
        try:
            async with httpx.AsyncClient(
                timeout=settings.INTERNAL_REQUEST_TIMEOUT_SECONDS
            ) as client:
                response = await client.request(
                    method,
                    f"{settings.WORKER_URL.rstrip('/')}/{path.lstrip('/')}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                    json=payload,
                )
        except httpx.HTTPError as error:
            raise WorkerClientError() from error
        if response.status_code >= 400:
            raise WorkerClientError(response.status_code)
        try:
            return response.json()
        except ValueError as error:
            raise WorkerClientError(response.status_code) from error

    async def enqueue(self, payload: dict):
        return await self.request(
            "POST", "/xu-ly-nen/noi-bo/kiem-thu/tac-vu", payload
        )

    async def get(self, job_id: str):
        return await self.request("GET", f"/xu-ly-nen/noi-bo/tac-vu/{job_id}")

    async def retry(self, job_id: str):
        return await self.request(
            "POST", f"/xu-ly-nen/noi-bo/tac-vu/{job_id}/thu-lai"
        )

    async def cancel(self, job_id: str):
        return await self.request("POST", f"/xu-ly-nen/noi-bo/tac-vu/{job_id}/huy")


worker_client = WorkerClient()
