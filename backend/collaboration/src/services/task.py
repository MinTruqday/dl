import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService

class TaskService:
    @staticmethod
    @log_logic_execution
    async def create_task(
        document_id: str,
        task_desc: str,
        assigned_to: str | None,
        current_user,
    ) -> dict:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        task_doc = {
            "_id": str(uuid.uuid4()),
            "document_id": document_id,
            "task_desc": task_desc,
            "created_by": str(current_user.id),
            "created_by_name": current_user.full_name,
            "assigned_to": assigned_to,
            "is_done": False,
            "created_at": datetime.now(timezone.utc),
        }
        await CooperationRepository.insert_task(task_doc)
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Create task",
            f"Created task: {task_desc[:30]}",
        )
        return {
            "id": task_doc["_id"],
            "task_desc": task_desc,
            "assigned_to": assigned_to,
            "is_done": False,
            "created_at": task_doc["created_at"].isoformat(),
            "message": "Tạo nhiệm vụ thành công",
        }

    @staticmethod
    @log_logic_execution
    async def get_tasks(document_id: str, current_user) -> list:
        doc = await DocumentRepository.find_one(
            {
                "_id": document_id,
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        tasks = (
            await mongo
            .find("collaboration_tasks", {"document_id": document_id})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return [
            {
                "id": t["_id"],
                "task_desc": t["task_desc"],
                "created_by": t.get("created_by"),
                "created_by_name": t.get("created_by_name"),
                "assigned_to": t.get("assigned_to"),
                "is_done": t.get("is_done", False),
                "created_at": (
                    t["created_at"].isoformat()
                    if isinstance(t.get("created_at"), datetime)
                    else t.get("created_at")
                ),
            }
            for t in tasks
        ]

    @staticmethod
    @log_logic_execution
    async def update_task(
        task_id: str, is_done: bool, current_user
    ) -> dict:
        task = await CooperationRepository.find_task({"_id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ")
        doc = await DocumentRepository.find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Không có quyền cập nhật nhiệm vụ này"
            )
        await CooperationRepository.update_task(
            {"_id": task_id},
            {"$set": {"is_done": is_done, "updated_at": datetime.now(timezone.utc)}},
        )
        await ActivityService.log_activity(
            task["document_id"],
            current_user.full_name,
            "Update task",
            f"Marked task as {'completed' if is_done else 'pending'}",
        )
        return {"message": "Cập nhật trạng thái nhiệm vụ thành công"}

    @staticmethod
    @log_logic_execution
    async def add_task_comment(
        task_id: str, comment_text: str, current_user
    ) -> dict:
        task = await CooperationRepository.find_task({"_id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ")
        doc = await DocumentRepository.find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Không có quyền bình luận nhiệm vụ này"
            )
        comment_doc = {
            "_id": str(uuid.uuid4()),
            "task_id": task_id,
            "user_id": str(current_user.id),
            "user_name": current_user.full_name,
            "comment_text": comment_text,
            "timestamp": datetime.now(timezone.utc),
        }
        await CooperationRepository.insert_task_comment(comment_doc)
        return {
            "id": comment_doc["_id"],
            "comment_text": comment_text,
            "user_name": current_user.full_name,
            "timestamp": comment_doc["timestamp"].isoformat(),
            "message": "Thêm bình luận nhiệm vụ thành công",
        }

    @staticmethod
    @log_logic_execution
    async def get_task_comments(task_id: str, current_user) -> list:
        task = await CooperationRepository.find_task({"_id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhiệm vụ")
        doc = await DocumentRepository.find_one(
            {
                "_id": task["document_id"],
                "$or": [
                    {"creator_id": str(current_user.id)},
                    {"coauthors": str(current_user.id)},
                ],
            }
        )
        if not doc:
            raise HTTPException(
                status_code=403, detail="Không có quyền xem bình luận nhiệm vụ này"
            )
        comments = (
            await mongo
            .find("collaboration_task_comments", {"task_id": task_id})
            .sort("timestamp", 1)
            .to_list(length=100)
        )
        return [
            {
                "id": c["_id"],
                "user_id": c["user_id"],
                "user_name": c["user_name"],
                "comment_text": c["comment_text"],
                "timestamp": (
                    c["timestamp"].isoformat()
                    if isinstance(c.get("timestamp"), datetime)
                    else c.get("timestamp")
                ),
            }
            for c in comments
        ]
