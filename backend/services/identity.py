from datetime import datetime
import uuid
from fastapi import HTTPException
from core.database import db_client
from models.user import AuthorStatusEnum, KYCStatusEnum
from core.storage import upload_file
from loguru import logger

class IdentityService:
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
