from core.database import db_client
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime
import json
import uuid
from loguru import logger
from models.user import AuthorStatusEnum, KYCStatusEnum
from core.storage import upload_file

class ProfileService:
    @staticmethod
    async def request_data_takeout(current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        comments = await db["comments"].find({"user_id": user_id}).to_list(length=1000)
        documents = await db["documents"].find({"author_id": user_id}).to_list(length=1000)
        reactions = await db["reactions"].find({"user_id": user_id}).to_list(length=1000)
        
        takeout_payload = {
            "profile": current_user.model_dump(exclude={"password_hash"}),
            "authored_documents": [{"id": str(b["_id"]), "title": b.get("title")} for b in documents],
            "comments_written": len(comments),
            "reactions_given": len(reactions),
            "raw_comments": [{"document_id": c.get("document_id"), "content": c.get("content")} for c in comments]
        }
        logger.info(f"Data takeout requested by user {user_id}")
        return takeout_payload

    @staticmethod
    async def apply_author(application, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        
        if current_user.author_status == AuthorStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Đơn đăng ký của bạn đang được xét duyệt.")
        if current_user.author_status == AuthorStatusEnum.SUSPENDED:
            raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị đình chỉ quyền tác giả.")
        if current_user.author_status == AuthorStatusEnum.APPROVED:
            raise HTTPException(status_code=400, detail="Bạn đã là tác giả.")
            
        application_data = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "portfolio_url": application.portfolio_url,
            "reason": application.reason,
            "status": AuthorStatusEnum.PENDING,
            "created_at": datetime.utcnow()
        }
        
        await db["author_applications"].insert_one(application_data)
        await db["users"].update_one(
            {"_id": user_id},
            {"$set": {
                "author_status": AuthorStatusEnum.PENDING,
                "tos_accepted_at": datetime.utcnow()
            }}
        )
        logger.info(f"Author application submitted by user {user_id}")
        return {"status": "success", "message": "Đã gửi đơn đăng ký tác giả."}

    @staticmethod
    async def upload_kyc(file, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        
        if current_user.kyc_status == KYCStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Tài liệu KYC đang được xem xét.")
        if current_user.kyc_status == KYCStatusEnum.VERIFIED:
            raise HTTPException(status_code=400, detail="Tài khoản đã được xác minh KYC.")
            
        file_bytes = await file.read()
        file_ext = file.filename.split(".")[-1]
        object_name = f"kyc/{user_id}_{uuid.uuid4()}.{file_ext}"
        
        await upload_file(file_bytes, object_name, content_type=file.content_type)
        
        kyc_data = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "document_url": object_name,
            "status": KYCStatusEnum.PENDING,
            "created_at": datetime.utcnow()
        }
        
        await db["kyc_applications"].insert_one(kyc_data)
        await db["users"].update_one(
            {"_id": user_id},
            {"$set": {"kyc_status": KYCStatusEnum.PENDING}}
        )
        logger.info(f"KYC document uploaded by user {user_id}")
        return {"status": "success", "message": "Đã tải lên tài liệu KYC."}

    @staticmethod
    async def right_to_be_forgotten(current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        
        await db["comments"].update_many(
            {"user_id": user_id},
            {"$set": {
                "content": "[Nội dung đã bị xóa theo yêu cầu của Quyền lãng quên GDPR]",
                "is_shadowbanned_content": True
            }}
        )
        
        await db["documents"].delete_many({"author_id": user_id})
        await db["reactions"].delete_many({"user_id": user_id})
        
        if db_client.redis:
            await db_client.redis.delete(f"active_session:{user_id}")
            
        await db["users"].delete_one({"_id": current_user.id})
        logger.info(f"User {user_id} requested to be forgotten (GDPR)")
        return {"status": "success", "message": "Tài khoản của bạn đã được xóa hoàn toàn khỏi hệ thống theo yêu cầu."}

    @staticmethod
    async def get_reading_streaks(current_user):
        db = db_client.mongodb.get_default_database()
        user_record = await db["users"].find_one({"_id": current_user.id})
        if not user_record:
            return {"current_streak": 0, "longest_streak": 0, "message": "Chưa có thông tin chuỗi đọc."}
            
        reading_stats = user_record.get("reading_stats", {})
        current_s = reading_stats.get("current_streak", 0)
        longest_s = reading_stats.get("longest_streak", 0)
        
        return {
            "current_streak": current_s,
            "longest_streak": longest_s,
            "message": f"Tuyệt vời! Bạn đang có chuỗi {current_s} ngày đọc tài liệu." if current_s > 0 else "Hãy bắt đầu đọc tài liệu ngay hôm nay để tích điểm chuỗi!"
        }

    @staticmethod
    async def update_profile(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        update_fields = {}
        if "full_name" in data and data["full_name"].strip():
            update_fields["full_name"] = data["full_name"].strip()
        if "bio" in data:
            update_fields["bio"] = data["bio"][:500]
        if "social_links" in data:
            update_fields["social_links"] = data["social_links"]
        if "donation_link" in data:
            update_fields["donation_link"] = data["donation_link"]
        if not update_fields:
            raise HTTPException(status_code=400, detail="Không có thông tin nào để cập nhật.")
        update_fields["updated_at"] = datetime.utcnow()
        await db["users"].update_one(
            {"_id": str(current_user.id)},
            {"$set": update_fields}
        )
        logger.info(f"Profile updated for user {current_user.id}")
        return {"message": "Đã cập nhật hồ sơ cá nhân."}

    @staticmethod
    async def get_user_profile(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)}, {"password_hash": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ.")
        user["_id"] = str(user["_id"])
        return user

    @staticmethod
    async def get_badges(current_user):
        db = db_client.mongodb.get_default_database()
        user_record = await db["users"].find_one({"_id": current_user.id})
        badges = user_record.get("badges", [])
        return {"badges": badges}

    @staticmethod
    async def block_user(target_id, current_user):
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": current_user.id},
            {"$addToSet": {"blocked_users": target_id}}
        )
        logger.info(f"User {current_user.id} blocked user {target_id}")
        return {"message": "Đã chặn người dùng."}

    @staticmethod
    async def request_data_export(current_user):
        logger.info(f"Data export request recorded for user {current_user.id}")
        return {"message": "Đã ghi nhận yêu cầu trích xuất dữ liệu. Sẽ gửi qua email trong vòng 24 giờ."}

    @staticmethod
    async def generate_gdpr_takeout(current_user):
        from core.publisher import publish_event
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        
        await publish_event("user_notifications", {"user_id": user_id, "message": "Đang chuẩn bị dữ liệu. Vui lòng chờ."})
        
        full_data = {
            "profile": await db["users"].find_one({"_id": current_user.id}, {"password_hash": 0}),
            "documents": await db["documents"].find({"author_id": user_id}).to_list(100),
            "comments": await db["comments"].find({"user_id": user_id}).to_list(500)
        }
        
        logger.info(f"GDPR takeout prepared for user {user_id}")
        await publish_event("user_notifications", {"user_id": user_id, "message": "Liên kết tải dữ liệu đã sẵn sàng.", "data": full_data})
        return {"status": "processing", "message": "Đang chuẩn bị dữ liệu. Vui lòng chờ."}

    @staticmethod
    async def toggle_bookmark(document_id, current_user):
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        user = await db["users"].find_one({"_id": user_id})
        bookmarks = user.get("bookmarks", [])
        if document_id in bookmarks:
            await db["users"].update_one({"_id": user_id}, {"$pull": {"bookmarks": document_id}})
            return {"status": "unbookmarked", "message": "Đã xóa khỏi danh sách lưu trữ."}
        await db["users"].update_one({"_id": user_id}, {"$addToSet": {"bookmarks": document_id}})
        return {"status": "bookmarked", "message": "Đã thêm vào danh sách lưu trữ."}

    @staticmethod
    async def get_bookmarks(current_user):
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)})
        bookmark_ids = user.get("bookmarks", [])
        documents = await db["documents"].find({"_id": {"$in": bookmark_ids}}).to_list(length=100)
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        return documents

    @staticmethod
    async def update_brand_page(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        update_fields = {}
        if "cover_image_url" in data:
            update_fields["author_profile.cover_image_url"] = data["cover_image_url"]
        if "welcome_video_url" in data:
            update_fields["author_profile.welcome_video_url"] = data["welcome_video_url"]
        if "custom_theme" in data:
            update_fields["author_profile.custom_theme"] = data["custom_theme"]
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="Không có thông tin nào để cập nhật.")
            
        update_fields["updated_at"] = datetime.utcnow()
        await db["users"].update_one({"_id": str(current_user.id)}, {"$set": update_fields})
        logger.info(f"Profile: Brand page updated for author {current_user.id}")
        return {"message": "Cập nhật trang tác giả cá nhân thành công."}

    @staticmethod
    async def get_author_public_profile(slug: str) -> dict:
        db = db_client.mongodb.get_default_database()
        author = await db["users"].find_one({"slug": slug, "role": "AUTHOR", "is_active": True})
        if not author:
            raise HTTPException(status_code=404, detail="Không tìm thấy trang tác giả.")
            
        author_id = str(author["_id"])
        docs = await db["documents"].find({"author_id": author_id, "status": "PUBLISHED"}).sort("created_at", -1).limit(10).to_list(length=10)
        
        return {
            "id": author_id,
            "full_name": author.get("full_name", "Tác giả ẩn danh"),
            "avatar_url": author.get("avatar_url"),
            "bio": author.get("bio", ""),
            "cover_image_url": author.get("author_profile", {}).get("cover_image_url"),
            "welcome_video_url": author.get("author_profile", {}).get("welcome_video_url"),
            "custom_theme": author.get("author_profile", {}).get("custom_theme"),
            "recent_documents": [{
                "id": str(d["_id"]),
                "title": d.get("title"),
                "slug": d.get("slug"),
                "cover_url": d.get("cover_url")
            } for d in docs]
        }