from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger

class ModeratorService:
    @staticmethod
    async def resolve_copyright_dispute(dispute_id: str, resolution: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["copyright_disputes"].update_one(
            {"_id": dispute_id}, 
            {"$set": {
                "status": "resolved", 
                "resolution": resolution, 
                "resolved_by": str(current_moderator.id), 
                "resolved_at": datetime.utcnow()
            }}
        )
        logger.info(f"Moderation: Copyright dispute {dispute_id} resolved by {current_moderator.id}")
        return {"message": "Đã giải quyết tranh chấp bản quyền thành công."}

    @staticmethod
    async def handle_bug_report(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        report_id = str(uuid.uuid4())
        await db["bug_reports"].insert_one({
            "_id": report_id, 
            "title": data["title"], 
            "description": data["description"], 
            "status": "open", 
            "assigned_to": str(current_moderator.id), 
            "created_at": datetime.utcnow()
        })
        logger.info(f"Support: Bug report {report_id} handled by {current_moderator.id}")
        return {"message": "Đã tiếp nhận báo cáo lỗi thành công."}

    @staticmethod
    async def assign_task(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        task = {
            "_id": str(uuid.uuid4()), 
            "assigned_to": data["moderator_id"], 
            "title": data["title"], 
            "status": "pending", 
            "created_at": datetime.utcnow()
        }
        await db["moderator_tasks"].insert_one(task)
        logger.info(f"System: Task assigned to {data['moderator_id']} by {current_moderator.id}")
        return {"message": "Đã phân công nhiệm vụ điều hành."}

    @staticmethod
    async def submit_policy_proposal(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        proposal_id = str(uuid.uuid4())
        await db["policy_proposals"].insert_one({
            "_id": proposal_id, 
            "author_id": str(current_moderator.id), 
            "title": data["title"], 
            "content": data["content"], 
            "status": "pending", 
            "created_at": datetime.utcnow()
        })
        logger.info(f"System: Policy proposal {proposal_id} submitted by {current_moderator.id}")
        return {"message": "Đề xuất chính sách đã được ghi nhận."}
