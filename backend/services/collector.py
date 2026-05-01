from typing import Any, Optional, List
from core.database import db_client
from core.publisher import publish_event
from fastapi import HTTPException
from loguru import logger
import uuid
from datetime import datetime

class CollectorService:
    @staticmethod
    async def trigger_collection(source: str, url: Optional[str] = None, index_type: Optional[str] = None, target_class: Optional[str] = None):
        if not db_client.rabbitmq:
            raise HTTPException(status_code=503, detail="Dịch vụ hàng đợi RabbitMQ hiện không sẵn sàng.")

        payload = {
            "source": source,
            "job_id": str(uuid.uuid4()),
            "triggered_at": datetime.utcnow().isoformat()
        }

        queue_name = ""
        if source == "AnnaArchive":
            queue_name = "collect_list_queue" if index_type == "list" else "collect_detail_queue"
            payload["url"] = url
            payload["index_type"] = index_type
        elif source == "NXBST":
            queue_name = "nxbst_queue"
            payload["url"] = url
        elif source == "NXBGDC":
            queue_name = "nxbgd_queue"
            payload["target_class"] = target_class or "10"
        else:
            raise HTTPException(status_code=400, detail=f"Nguồn thu thập '{source}' không được hỗ trợ.")

        success = await publish_event(queue_name, payload)
        if not success:
            raise HTTPException(status_code=500, detail="Không thể gửi lệnh thu thập vào hàng đợi xử lý.")
        
        logger.info(f"Collection job {payload['job_id']} triggered for source {source}")
        return {"status": "success", "job_id": payload["job_id"], "message": f"Đã kích hoạt tiến trình thu thập dữ liệu từ {source}."}

    @staticmethod
    async def get_collector_stats():
        db = db_client.mongodb.get_default_database()
        total_collected = await db["documents"].count_documents({"author_id": {"$regex": ".*collector.*"}})
        return {
            "total_documents_collected": total_collected,
            "active_sources": ["AnnaArchive", "NXBST", "NXBGDC"],
            "status": "operational"
        }
