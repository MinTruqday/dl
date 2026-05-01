from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
from loguru import logger
from bson import ObjectId

class AuthorService:
    @staticmethod
    async def update_brand_page(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        update = {
            "brand_tagline": data.get("tagline", "")[:200],
            "brand_about": data.get("about", "")[:2000],
            "brand_links": data.get("links", {}),
            "welcome_message": data.get("welcome_message", "")[:1000],
            "updated_at": datetime.utcnow(),
        }
        await db["users"].update_one({"_id": str(current_user.id)}, {"$set": update})
        logger.info(f"Identity: Author {current_user.id} updated brand page profile")
        return {"message": "Đã cập nhật trang thương hiệu và lời chào thành công."}

    @staticmethod
    async def reply_to_review(review_id: str, reply_text: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        review = await db["reviews"].find_one({"_id": ObjectId(review_id)})
        if not review:
            raise HTTPException(status_code=404, detail="Bản đánh giá không tồn tại.")
        
        doc = await db["documents"].find_one({"_id": review["document_id"]})
        if not doc or (doc["author_id"] != str(current_user.id) and str(current_user.id) not in doc.get("coauthors", [])):
            raise HTTPException(status_code=403, detail="Bạn không có quyền phản hồi đánh giá cho tài liệu này.")
            
        await db["reviews"].update_one(
            {"_id": ObjectId(review_id)},
            {"$set": {"author_reply": reply_text, "replied_at": datetime.utcnow()}}
        )
        logger.info(f"Workspace: Author {current_user.id} replied to review {review_id}")
        return {"message": "Đã gửi phản hồi thành công."}

    @staticmethod
    async def apply_for_author(motivation: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        if current_user.role in ["AUTHOR", "ADMIN"]:
            raise HTTPException(status_code=400, detail="Bạn đã có quyền tác giả.")
        
        existing = await db["author_applications"].find_one({"user_id": str(current_user.id), "status": "PENDING"})
        if existing:
            raise HTTPException(status_code=400, detail="Bạn đã có một đơn ứng tuyển đang chờ xử lý.")
        
        application = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "user_name": current_user.full_name or current_user.username,
            "user_email": current_user.email,
            "motivation": motivation,
            "status": "PENDING",
            "created_at": datetime.utcnow()
        }
        await db["author_applications"].insert_one(application)
        logger.info(f"Identity: Author application submitted by {current_user.id}")
        return {"message": "Đã gửi đơn ứng tuyển thành công."}
