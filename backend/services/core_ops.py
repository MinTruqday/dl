from core.database import db_client
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime
import json
import re
from loguru import logger

class CoreOpsService:

    @staticmethod
    async def global_find_replace(document_id, payload, current_user):
        db = db_client.mongodb.get_default_database()
        search_term = payload.get("search")
        replace_term = payload.get("replace")
        match_case = payload.get("match_case", False)
        
        if not search_term or not replace_term:
            raise HTTPException(status_code=400, detail="Thiếu thông tin cần thiết.")
            
        user_id = str(current_user.id)
        document = await db["documents"].find_one({"_id": str(document_id), "author_id": user_id})
        if not document:
            raise HTTPException(status_code=403, detail="Không có quyền thao tác hoặc tài liệu không tồn tại")
            
        flags = 0 if match_case else re.IGNORECASE
        pattern = re.compile(re.escape(search_term), flags=flags)
        
        new_title = pattern.sub(replace_term, document.get("title", ""))
        new_desc = pattern.sub(replace_term, document.get("description", ""))
        new_content = None
        
        if document.get("content"):
            content_str = json.dumps(document["content"])
            new_content_str = pattern.sub(replace_term, content_str)
            try:
                new_content = json.loads(new_content_str)
            except Exception as e:
                logger.error(f"Regex JSON load failed for globally replacing content: {e}")
                new_content = None
                
        update_data = {
            "title": new_title, 
            "description": new_desc, 
            "updated_at": datetime.utcnow()
        }
        if new_content:
            update_data["content"] = new_content
            
        await db["documents"].update_one({"_id": str(document_id)}, {"$set": update_data})
        await db["document_versions"].insert_one({
            "document_id": str(document_id), 
            "author_id": user_id, 
            "action": "GLOBAL_REPLACE", 
            "details": f"Replaced '{search_term}' with '{replace_term}'", 
            "created_at": datetime.utcnow()
        })
        return {"message": "Thay thế toàn cục thành công", "affected_fields": ["title", "description", "content"]}

    @staticmethod
    async def generate_gdpr_takeout(background_tasks, current_user):
        from core.publisher import publish_event
        user_id = str(current_user.id)
        await publish_event("user_notifications", {"user_id": user_id, "message": "Đang chuẩn bị dữ liệu. Vui lòng chờ."})

        async def process_takeout(uid: str):
            db = db_client.mongodb.get_default_database()
            full_data = {
                "profile": await db["users"].find_one({"_id": uid}, {"password_hash": 0}), 
                "documents": await db["documents"].find({"author_id": uid}).to_list(100), 
                "comments": await db["comments"].find({"user_id": uid}).to_list(500), 
                "wallet_txs": await db["transactions"].find({"user_id": uid}).to_list(500)
            }
            await publish_event("user_notifications", {"user_id": uid, "message": "Liên kết tải dữ liệu đã sẵn sàng.", "data": full_data})
            
        background_tasks.add_task(process_takeout, user_id)
        return {"status": "processing", "message": "Đang chuẩn bị dữ liệu. Vui lòng chờ."}

    @staticmethod
    async def right_to_be_forgotten(current_user):
        db = db_client.mongodb.get_default_database()
        uid = str(current_user.id)
        await db["users"].update_one(
            {"_id": uid}, 
            {"$set": {
                "email": f"deleted_{uid}@gdpr.mask", 
                "full_name": "[User đã xóa]", 
                "password_hash": "", 
                "status": "gdpr_deleted", 
                "updated_at": datetime.utcnow()
            }}
        )
        await db["comments"].update_many(
            {"user_id": uid}, 
            {"$set": {
                "content_anonymized": True, 
                "content": "[Bình luận này đã bị xóa bởi quyền lãng quên (GDPR Right to be Forgotten)]"
            }}
        )
        return {"message": "Đã xóa tài khoản."}