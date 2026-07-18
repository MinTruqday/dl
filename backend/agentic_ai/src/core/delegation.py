import uuid
import asyncio
import json
import requests
from loguru import logger
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis

class ToolDelegator:
    @staticmethod
    async def delegate(action: str, payload: dict, timeout: float = 30.0) -> str:
        task_id = str(uuid.uuid4())
        channel = f"tool_result:{task_id}"
        
        pubsub = redis.get_client().pubsub()
        await pubsub.subscribe(channel)
        
        try:
            requests.post(
                f"{settings.WEBSOCKET_URL}/ws/broadcast",
                json={
                    "document_id": "global",
                    "message": {
                        "type": "TOOL_EXECUTION_REQUEST",
                        "task_id": task_id,
                        "action": action,
                        "payload": payload
                    }
                },
                timeout=2.0
            )
        except Exception as e:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.error(f"MODULE AGENTIC_AI: Failed to broadcast delegation: {e}")
            raise Exception("Hệ thống mất kết nối với giao diện máy khách")

        try:
            async def _wait_for_message():
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        return message["data"]
            
            result = await asyncio.wait_for(_wait_for_message(), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.warning(f"MODULE AGENTIC_AI: Delegation {action} timed out after {timeout}s")
            return f"Lỗi thực thi: Không nhận được phản hồi từ trình duyệt sau {timeout} giây."
        except Exception as e:
            logger.error(f"MODULE AGENTIC_AI: Delegation error: {e}")
            return "Lỗi hệ thống khi chờ kết quả xử lý."
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

delegator = ToolDelegator()
