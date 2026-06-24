import httpx
from loguru import logger
from typing import Any, Dict, Optional

class QueueAPIClient:
    def __init__(self, base_url: str = "http://doclib_queue:8802/hang-doi"):
        self.base_url = base_url

    async def _post(self, path: str, json_data: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.base_url}{path}", json=json_data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Lỗi gọi Queue API POST {path}: {e}")
            return {}

    async def _get(self, path: str, params: dict = None, timeout: int = 35) -> dict:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{self.base_url}{path}", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.ReadTimeout:
            return {}
        except Exception as e:
            logger.error(f"Lỗi gọi Queue API GET {path}: {e}")
            return {}

    async def publish(self, queue_name: str, payload: Dict[str, Any]) -> bool:
        res = await self._post("/xuat-ban", {"queue_name": queue_name, "payload": payload})
        return res.get("status") == "success"

    async def consume(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        res = await self._get(f"/tieu-thu/{queue_name}", params={"timeout": timeout}, timeout=timeout+5)
        return res.get("data")

mq = QueueAPIClient()
