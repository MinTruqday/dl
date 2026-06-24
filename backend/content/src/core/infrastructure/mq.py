from src.core.infrastructure.configuration import settings
import httpx
from loguru import logger
from typing import Any, Dict, Optional

class QueueAPIClient:
    def __init__(self, base_url: str = settings.QUEUE_URL):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def _post(self, path: str, json_data: dict) -> dict:
        try:
            response = await self._client.post(path, json=json_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Lỗi gọi Queue API POST {path}: {e}")
            raise e

    async def _get(self, path: str, params: dict = None, timeout: int = 35) -> dict:
        try:
            response = await self._client.get(path, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except httpx.ReadTimeout:
            logger.warning(f"Timeout gọi Queue API GET {path}")
            raise Exception("Timeout")
        except Exception as e:
            logger.error(f"Lỗi gọi Queue API GET {path}: {e}")
            raise e

    async def publish(self, queue_name: str, payload: Dict[str, Any]) -> bool:
        res = await self._post("/xuat-ban", {"queue_name": queue_name, "payload": payload})
        return res.get("status") == "success"

    async def consume(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        res = await self._get(f"/tieu-thu/{queue_name}", params={"timeout": timeout}, timeout=timeout+5)
        return res.get("data")


    
    async def ack(self, delivery_tag: str) -> bool:
        res = await self._post("/xac-nhan", {"delivery_tag": delivery_tag})
        return res.get("status") == "success"

    async def health_check(self) -> bool:
        try:
            res = await self._get("/health", timeout=5)
            return res.get("status") == "ok"
        except Exception:
            return False

    async def aclose(self):
        await self._client.aclose()

mq = QueueAPIClient()
