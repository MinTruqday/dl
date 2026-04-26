from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import json
import uuid
from loguru import logger

class ModerationService:
    @staticmethod
    async def ai_analyze_content(text: str):
        if not text or not text.strip():
            return {"is_toxic": False, "detected_keywords": [], "confidence_score": 0.0}
        
        import os
        import httpx
        rag_url = os.environ.get("AGENTIC_RAG_URL")
        if not rag_url:
            return {"is_toxic": False, "detected_keywords": [], "confidence_score": 0.0}

        try:
            prompt = f"Phân tích đoạn văn bản sau đây xem có chứa nội dung độc hại, xúc phạm, lừa đảo, phản động, hoặc spam không. Trả về đúng định dạng JSON với 3 trường: 'is_toxic' (boolean), 'detected_keywords' (mảng chuỗi), 'confidence_score' (số thực từ 0.0 đến 1.0). Chỉ trả về JSON, không giải thích thêm.\nVăn bản: '{text}'"
            
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"{rag_url}/api/inference/generate_raw",
                    json={"prompt": prompt, "max_tokens": 150, "temperature": 0.1},
                    timeout=10.0
                )
                res.raise_for_status()
                text_resp = res.json().get("result", "")
                if text_resp.startswith("```json"):
                    text_resp = text_resp[7:-3]
                elif text_resp.startswith("```"):
                    text_resp = text_resp[3:-3]
                    
                result = json.loads(text_resp)
                return {
                    "is_toxic": bool(result.get("is_toxic", False)),
                    "detected_keywords": result.get("detected_keywords", []),
                    "confidence_score": float(result.get("confidence_score", 0.1))
                }
        except Exception as e:
            logger.error(f"AI moderation HTTP error: {e}")
            return {"is_toxic": False, "detected_keywords": [], "confidence_score": 0.0}

    @staticmethod
    async def report_content(req, current_user):
        db = db_client.mongodb.get_default_database()
        
        ai_meta = await ModerationService.ai_analyze_content(req.description or "")
        
        report_doc = {
            "_id": str(uuid.uuid4()),
            "reporter_id": current_user.id,
            "item_type": req.item_type,
            "item_id": req.item_id,
            "reason": req.reason,
            "description": req.description,
            "status": "pending",
            "ai_flag": ai_meta["is_toxic"],
            "ai_meta": ai_meta,
            "created_at": datetime.utcnow()
        }
        await db["reports"].insert_one(report_doc)
        
        if db_client.redis:
            await db_client.redis.publish("admin_alerts", json.dumps({
                "title": "Cảnh báo vi phạm" + (" (AI Flagged)" if ai_meta["is_toxic"] else ""),
                "body": f"Nội dung {req.item_type} đã bị người dùng báo cáo: {req.reason}"
            }))
            
        logger.info(f"Content {req.item_type} {req.item_id} reported by user {current_user.id}. AI Flag: {ai_meta['is_toxic']}")
        return {"status": "success", "message": "Báo cáo của bạn đã được ghi nhận và đang được AI thẩm định."}

    @staticmethod
    async def get_pending_reports():
        db = db_client.mongodb.get_default_database()
        cursor = db["reports"].find({"status": "pending"}).sort("created_at", -1)
        return await cursor.to_list(length=50)

    @staticmethod
    async def resolve_report(report_id, action, current_admin):
        db = db_client.mongodb.get_default_database()
        report = await db["reports"].find_one({"_id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo.")
            
        target_collection = "books"
        if report["item_type"] == "comment":
            target_collection = "comments"
        elif report["item_type"] == "feed":
            target_collection = "posts"
        elif report["item_type"] == "review":
            target_collection = "reviews"

        if action.action == "takedown":
            if target_collection == "books":
                await db["documents"].update_one({"_id": report["item_id"]}, {"$set": {"status": "banned", "updated_at": datetime.utcnow()}})
            elif target_collection == "posts":
                await db["posts"].update_one({"_id": report["item_id"]}, {"$set": {"status": "removed", "is_active": False, "updated_at": datetime.utcnow()}})
            elif target_collection == "reviews":
                await db["reviews"].update_one({"_id": report["item_id"]}, {"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
            else:
                await db["comments"].update_one(
                    {"_id": report["item_id"]}, 
                    {"$set": {"is_shadowbanned_content": True, "content": "[Nội dung đã bị xóa do vi phạm tiêu chuẩn cộng đồng]", "updated_at": datetime.utcnow()}}
                )
        elif action.action == "shadowban_user":
            target_item = await db[target_collection].find_one({"_id": report["item_id"]})
            if target_item:
                author_field = "user_id"
                if target_collection == "books":
                    author_field = "author_id"
                
                bad_user_id = target_item.get(author_field)
                if bad_user_id:
                    await db["users"].update_one({"_id": bad_user_id}, {"$set": {"is_shadowbanned": True, "updated_at": datetime.utcnow()}})
                    if target_collection == "comments":
                        await db["comments"].update_one({"_id": report["item_id"]}, {"$set": {"is_shadowbanned_content": True, "updated_at": datetime.utcnow()}})
                        
        await db["reports"].update_one(
            {"_id": report_id},
            {"$set": {
                "status": "resolved",
                "resolved_by": current_admin.id,
                "resolution_action": action.action,
                "resolved_at": datetime.utcnow()
            }}
        )
        
        await db["audit_logs"].insert_one({
            "action": "MODERATE_REPORT",
            "actor_email": current_admin.email,
            "report_id": report_id,
            "resolution": action.action,
            "timestamp": datetime.utcnow()
        })
        
        logger.info(f"Report {report_id} resolved by admin {current_admin.id} with action {action.action}")
        return {"status": "success", "message": f"Đã giải quyết báo cáo với hành động: {action.action}"}